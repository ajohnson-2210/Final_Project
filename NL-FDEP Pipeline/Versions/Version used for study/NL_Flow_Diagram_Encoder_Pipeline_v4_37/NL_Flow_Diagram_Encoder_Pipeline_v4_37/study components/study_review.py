"""Integrated questionnaire-driven human-review session and Tk dashboard.

The dashboard is intentionally LLM-only. Baseline algorithms are calibration
artefacts and are excluded from human-review discovery.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
import json
import os
import re
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from adjudication import adjudicate_files
from human_review import _html_document


_SCORE_LABELS = ("2", "1", "0", "NA")
_AGREEMENT_VALUES = ("AGREE", "PARTIALLY_AGREE", "DISAGREE")


REVIEW_STATE_SCHEMA_VERSION = "1.0"
REVIEW_STATE_PURPOSE = "HUMAN_REVIEW_PREVIOUS_STUDY_HINT"
REVIEW_STATE_FILE_ENV = "NL_FDEP_HUMAN_REVIEW_STATE_FILE"


def _review_state_path() -> Path:
    """Return the durable, non-scoring Human Review discovery-state path."""
    override = os.environ.get(REVIEW_STATE_FILE_ENV)
    if override:
        return Path(override).expanduser()

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "NL-FDEP" / "human_review_state.json"

    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home) / "NL-FDEP" / "human_review_state.json"

    return Path.home() / ".config" / "NL-FDEP" / "human_review_state.json"


def _study_parent_for_review_root(value: Path) -> Path | None:
    """Return the parent directory whose children are experimental dataset folders."""
    normalised = normalise_review_root(Path(value))
    if normalised is None:
        return None
    outer = normalised.parent if normalised.name.casefold() == "results" else normalised
    return outer.parent.resolve()


def remember_review_study(value: Path) -> Path | None:
    """Persist a harmless cross-session pointer used only for Human Review discovery.

    The file stores no baseline path, calibration state, score or review answer. It
    merely remembers the study parent so a later Human Review session can rebuild
    the experimental dataset selector from artefacts already present on disk.
    """
    study_parent = _study_parent_for_review_root(Path(value))
    if study_parent is None:
        return None
    payload = {
        "schema_version": REVIEW_STATE_SCHEMA_VERSION,
        "state_purpose": REVIEW_STATE_PURPOSE,
        "study_parent": str(study_parent),
    }
    path = _review_state_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    except OSError:
        return None
    return study_parent


def previous_study_review_roots() -> list[Path]:
    """Rebuild the last Human Review study selector without asking for an anchor.

    Only reviewable experimental LLM datasets are returned. Baseline artefacts are
    filtered by :func:`review_status`, exactly as in ordinary sibling discovery.
    """
    path = _review_state_path()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(payload, dict):
        return []
    if payload.get("state_purpose") != REVIEW_STATE_PURPOSE:
        return []
    raw_parent = payload.get("study_parent")
    if not isinstance(raw_parent, str) or not raw_parent.strip():
        return []
    study_parent = Path(raw_parent).expanduser()
    if not study_parent.is_dir():
        return []

    roots: list[Path] = []
    try:
        siblings = sorted(
            (child for child in study_parent.iterdir() if child.is_dir()),
            key=lambda child: child.name.casefold(),
        )
    except OSError:
        return []
    for sibling in siblings:
        candidate = normalise_review_root(sibling)
        if candidate is None or not review_status(candidate):
            continue
        roots.append(candidate.resolve())
    return roots


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def _algorithm_id_from_folder(folder: Path) -> int | None:
    try:
        return int(Path(folder).name.split("-")[-1].strip())
    except Exception:
        return None


def _direct_algorithm_folders(parent: Path) -> list[Path]:
    rows: list[tuple[int, Path]] = []
    for child in Path(parent).glob("Algorithm - *"):
        if not child.is_dir():
            continue
        aid = _algorithm_id_from_folder(child)
        if aid is not None:
            rows.append((aid, child))
    return [folder for _, folder in sorted(rows, key=lambda item: item[0])]


def normalise_review_root(selected_path: Path) -> Path | None:
    """Resolve an LLM review selection to the directory containing Algorithm folders.

    Accepted experimental layouts are either ``root/Algorithm - n`` or
    ``root/Results/Algorithm - n``. Baseline ``Pseudocode`` folders are
    deliberately not accepted for human review.
    """
    selected = Path(selected_path)
    if not selected.is_dir():
        return None
    if _direct_algorithm_folders(selected):
        return selected
    results_children = [
        child for child in selected.iterdir()
        if child.is_dir() and child.name.casefold() == "results"
    ]
    if len(results_children) == 1 and _direct_algorithm_folders(results_children[0]):
        return results_children[0]
    return None


def _questionnaire_for_algorithm(folder: Path) -> Path:
    return folder / "pipeline_artifacts" / "scoring" / "human_review_questionnaire.json"


def _is_baseline_questionnaire(document: dict[str, Any]) -> bool:
    algorithm = document.get("algorithm", {}) or {}
    if bool(algorithm.get("is_baseline")):
        return True
    return str(algorithm.get("dataset") or "").strip().casefold() == "baseline"


def _review_owner(document: dict[str, Any] | None) -> tuple[str, str]:
    reviewer = (document or {}).get("reviewer", {}) or {}
    return (
        str(reviewer.get("reviewer_id") or "").strip(),
        str(reviewer.get("reviewer_name") or "").strip(),
    )


def _review_completion(document: dict[str, Any] | None) -> tuple[str, int, int]:
    if not document:
        return "NOT_REVIEWED", 0, 16
    criteria = document.get("criteria", []) or []
    total = len(criteria) or 16
    completed = sum(
        1 for item in criteria
        if str(((item.get("human_assessment") or {}).get("score_label") or "")).upper() in _SCORE_LABELS
    )
    return ("COMPLETE" if total > 0 and completed == total else "IN_PROGRESS", completed, total)


def review_status(parent: Path) -> list[dict[str, Any]]:
    """Return numerically sorted review rows for one experimental dataset."""
    parent = Path(parent)
    rows: list[dict[str, Any]] = []
    for algorithm_folder in _direct_algorithm_folders(parent):
        aid = _algorithm_id_from_folder(algorithm_folder)
        scoring = algorithm_folder / "pipeline_artifacts" / "scoring"
        questionnaire = scoring / "human_review_questionnaire.json"
        if not questionnaire.is_file():
            continue
        document = _read_json(questionnaire) or {}
        if _is_baseline_questionnaire(document):
            continue
        review_path = scoring / "human_review.json"
        review_document = _read_json(review_path) if review_path.is_file() else None
        review_state, completed, total = _review_completion(review_document)
        reviewer_id, reviewer_name = _review_owner(review_document)
        rows.append({
            "algorithm_id": aid,
            "scoring_directory": str(scoring.resolve()),
            "questionnaire": True,
            "questionnaire_html": str((scoring / "human_review_questionnaire.html").resolve()) if (scoring / "human_review_questionnaire.html").is_file() else None,
            "reviewed": review_document is not None,
            "review_state": review_state,
            "reviewer_id": reviewer_id,
            "reviewer_name": reviewer_name,
            "criteria_completed": completed,
            "criteria_total": total,
            "final_score": (scoring / "final_score.json").exists(),
        })
    return sorted(rows, key=lambda row: (row.get("algorithm_id") is None, row.get("algorithm_id") or 10**9))


def _dataset_name(root: Path, rows: list[dict[str, Any]]) -> str:
    if rows:
        scoring = Path(rows[0]["scoring_directory"])
        q = _read_json(scoring / "human_review_questionnaire.json") or {}
        dataset = str((q.get("algorithm") or {}).get("dataset") or "").strip()
        if dataset and dataset.casefold() != "baseline":
            return dataset
    root = Path(root)
    return root.parent.name if root.name.casefold() == "results" else root.name


def discover_review_datasets(parents: Iterable[Path] | Path) -> list[dict[str, Any]]:
    """Build a de-duplicated experimental review registry from selected/session roots."""
    if isinstance(parents, (str, Path)):
        candidates = [Path(parents)]
    else:
        candidates = [Path(value) for value in parents]

    seen: set[str] = set()
    datasets: list[dict[str, Any]] = []
    for candidate in candidates:
        normalised = normalise_review_root(candidate)
        if normalised is None:
            continue
        key = str(normalised.resolve()).casefold()
        if key in seen:
            continue
        seen.add(key)
        rows = review_status(normalised)
        if not rows:
            continue
        datasets.append({
            "name": _dataset_name(normalised, rows),
            "root": str(normalised.resolve()),
            "rows": rows,
        })
    return datasets


def discover_sibling_review_roots(anchor: Path) -> list[Path]:
    """Reconstruct a review registry from sibling completed experimental datasets.

    ``anchor`` may be an outer LLM dataset folder or its ``Results`` directory.
    Only immediate sibling folders that contain reviewable experimental LLM
    questionnaires are returned. Baseline datasets are excluded by
    :func:`review_status`.
    """
    normalised = normalise_review_root(Path(anchor))
    if normalised is None:
        return []

    outer = normalised.parent if normalised.name.casefold() == "results" else normalised
    study_parent = outer.parent
    candidate_roots: list[Path] = []
    try:
        siblings = sorted(
            (child for child in study_parent.iterdir() if child.is_dir()),
            key=lambda child: child.name.casefold(),
        )
    except OSError:
        siblings = []

    for sibling in siblings:
        candidate = normalise_review_root(sibling)
        if candidate is None:
            continue
        if not review_status(candidate):
            continue
        candidate_roots.append(candidate.resolve())

    if not candidate_roots:
        return [normalised.resolve()] if review_status(normalised) else []

    # De-duplicate in case a filesystem layout exposes the same Results path twice.
    seen: set[str] = set()
    output: list[Path] = []
    for candidate in candidate_roots:
        key = str(candidate).casefold()
        if key in seen:
            continue
        seen.add(key)
        output.append(candidate)
    return output


class ReviewSession:
    """Load, resume and save one questionnaire-driven review."""

    def __init__(self, scoring_directory: Path):
        self.scoring_directory = Path(scoring_directory)
        q = self.scoring_directory / "human_review_questionnaire.json"
        if not q.is_file():
            raise FileNotFoundError(q)
        questionnaire = json.loads(q.read_text(encoding="utf-8"))
        if _is_baseline_questionnaire(questionnaire):
            raise ValueError("Baseline algorithms do not require human review.")
        saved = _read_json(self.scoring_directory / "human_review.json")
        self.document = saved if saved is not None else questionnaire
        self.questionnaire_html = self.scoring_directory / "human_review_questionnaire.html"

    def save(
        self,
        *,
        reviewer_id: str,
        confidence: str | None,
        reviewer_name: str = "",
        source_review: dict[str, Any] | None = None,
        evidence_review: dict[str, Any] | None = None,
        semantic_review: dict[str, Any] | None = None,
        criteria: dict[str, dict[str, Any]],
        overall: dict[str, Any],
        gate_result: str | None = None,
        gate_agreement: str | None = None,
        gate_justification: str = "",
        baseline_reference_appropriate: str | None = None,
        baseline_reference_justification: str = "",
    ) -> Path:
        reviewer_id = str(reviewer_id or "").strip()
        reviewer_name = str(reviewer_name or "").strip()
        if not reviewer_id:
            raise ValueError("Reviewer ID is required.")
        existing_path = self.scoring_directory / "human_review.json"
        existing = _read_json(existing_path) if existing_path.is_file() else None
        existing_id, existing_name = _review_owner(existing)
        if existing_id and existing_id != reviewer_id:
            raise PermissionError(f"This review belongs to reviewer {existing_id}; overwrite is blocked.")
        if existing_id == reviewer_id and existing_name and reviewer_name and existing_name != reviewer_name:
            raise PermissionError(
                f"Reviewer ID {reviewer_id} is already associated with {existing_name!r}; overwrite is blocked."
            )
        out = deepcopy(self.document)
        out["reviewer"] = {
            "reviewer_id": reviewer_id,
            "reviewer_name": reviewer_name or existing_name,
            "reviewed_at_utc": datetime.now(timezone.utc).isoformat(),
            "overall_reviewer_confidence": confidence,
        }

        source_review = source_review or {
            "human_result": gate_result,
            "agreement_with_automated_result": gate_agreement,
            "reviewer_justification": gate_justification,
        }
        evidence_review = evidence_review or {}

        ss = out.setdefault("source_sufficiency", {})
        ss["human_result"] = source_review.get("human_result")
        ss["agreement_with_automated_result"] = source_review.get("agreement_with_automated_result")
        ss["reviewer_justification"] = source_review.get("reviewer_justification", "")

        g2 = out.setdefault("behavioural_evidence_adequacy", {})
        g2["human_result"] = evidence_review.get("human_result")
        g2["agreement_with_automated_result"] = evidence_review.get("agreement_with_automated_result")
        g2["reviewer_justification"] = evidence_review.get("reviewer_justification", "")

        if out.get("task_semantic_evaluation") is not None and semantic_review is not None:
            human = out["task_semantic_evaluation"].setdefault("human_assessment", {})
            human.update({
                "required_inputs_represented": semantic_review.get("required_inputs_represented"),
                "core_algorithm_logic": semantic_review.get("core_algorithm_logic"),
                "required_output_semantics_represented": semantic_review.get("required_output_semantics_represented"),
                "edge_and_domain_handling": semantic_review.get("edge_and_domain_handling"),
                "overall_semantic_assessment": semantic_review.get("overall_semantic_assessment"),
                "reviewer_justification": semantic_review.get("reviewer_justification", ""),
            })

        for item in out.get("criteria", []):
            cid = item.get("criterion_id")
            values = criteria.get(str(cid), {})
            ha = item.setdefault("human_assessment", {})
            score_label = values.get("score_label")
            ha.update({
                "score": values.get("score"),
                "score_label": score_label,
                "agreement_with_automated_score": values.get("agreement_with_automated_score"),
                "semantic_issue": values.get("semantic_issue"),
                "reviewer_justification": values.get("reviewer_justification", ""),
                "completed": score_label in _SCORE_LABELS,
            })

        out.setdefault("overall_review", {}).update(overall)
        path = self.scoring_directory / "human_review.json"
        path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        adjudicate_files(self.scoring_directory)

        # Presentation-only refresh: keep the central dashboards in sync with
        # the just-saved human review. Dashboard failure must never block or
        # alter the authoritative review/adjudication artefacts.
        try:
            algorithm_folder = self.scoring_directory.parent.parent
            batch_root = algorithm_folder.parent
            analysis_directory = batch_root / "study_analysis"
            if analysis_directory.is_dir():
                from dashboard_generation import generate_dashboards_for_completed_batch
                generate_dashboards_for_completed_batch(batch_root, analysis_directory, "LLM_RESULTS")
        except Exception:
            pass

        self.document = out
        return path


def _study_wide_review_roots(parents: Iterable[Path] | Path) -> list[Path]:
    """Return reviewable experimental roots across the study areas represented."""
    if isinstance(parents, (str, Path)):
        initial = [Path(parents)]
    else:
        initial = [Path(value) for value in parents]
    roots: list[Path] = []
    seen: set[str] = set()
    for value in initial:
        normalised = normalise_review_root(value)
        if normalised is None:
            continue
        discovered = discover_sibling_review_roots(normalised) or [normalised]
        for candidate in discovered:
            key = str(candidate.resolve()).casefold()
            if key in seen:
                continue
            seen.add(key)
            roots.append(candidate.resolve())
    return roots


def reviewer_registry(parents: Iterable[Path] | Path) -> tuple[dict[str, str], list[str]]:
    """Build a study-wide reviewer-ID -> name registry from saved LLM reviews."""
    mapping: dict[str, str] = {}
    conflicts: list[str] = []
    for root in _study_wide_review_roots(parents):
        for row in review_status(root):
            scoring = Path(row["scoring_directory"])
            review = _read_json(scoring / "human_review.json")
            reviewer_id, reviewer_name = _review_owner(review)
            if not reviewer_id:
                continue
            previous = mapping.get(reviewer_id, "")
            if previous and reviewer_name and previous != reviewer_name:
                conflicts.append(
                    f"{reviewer_id} is associated with both {previous!r} and {reviewer_name!r}."
                )
                continue
            if reviewer_name or reviewer_id not in mapping:
                mapping[reviewer_id] = reviewer_name
    return mapping, conflicts


def next_reviewer_id(mapping: dict[str, str]) -> str:
    numbers = []
    for reviewer_id in mapping:
        match = re.fullmatch(r"REV(\d+)", reviewer_id.strip(), flags=re.IGNORECASE)
        if match:
            numbers.append(int(match.group(1)))
    number = (max(numbers) + 1) if numbers else 1
    return f"REV{number:03d}"


class _LocalReviewService:
    """Localhost-only service used by the authoritative HTML questionnaire."""

    def __init__(self, registry: dict[str, str]):
        self.registry = dict(registry)
        self.contexts: dict[str, dict[str, Any]] = {}
        handler = self._handler_type()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.server.review_service = self  # type: ignore[attr-defined]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def base_url(self) -> str:
        host, port = self.server.server_address[:2]
        return f"http://{host}:{port}"

    def stop(self) -> None:
        try:
            self.server.shutdown()
            self.server.server_close()
        except Exception:
            pass

    def register(self, scoring_directory: Path, reviewer_id: str, reviewer_name: str) -> str:
        token = secrets.token_urlsafe(24)
        self.contexts[token] = {
            "scoring_directory": str(Path(scoring_directory).resolve()),
            "reviewer_id": reviewer_id,
            "reviewer_name": reviewer_name,
        }
        return f"{self.base_url}/questionnaire/{token}"

    def _identity_error(self, reviewer_id: str, reviewer_name: str) -> str | None:
        known = self.registry.get(reviewer_id)
        if known and known != reviewer_name:
            return f"Reviewer ID {reviewer_id} is already associated with {known!r}."
        return None

    def _handler_type(self):
        service = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "NLFDEPReview/1.0"

            def log_message(self, format: str, *args) -> None:
                return

            def _json(self, status: int, payload: dict[str, Any]) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _context(self, prefix: str) -> tuple[str, dict[str, Any] | None]:
                path = urlparse(self.path).path
                token = path[len(prefix):] if path.startswith(prefix) else ""
                return token, service.contexts.get(token)

            def do_GET(self) -> None:
                token, context = self._context("/questionnaire/")
                if not token or context is None:
                    self.send_error(404)
                    return
                scoring = Path(context["scoring_directory"])
                questionnaire = _read_json(scoring / "human_review_questionnaire.json")
                if not questionnaire or _is_baseline_questionnaire(questionnaire):
                    self.send_error(404)
                    return
                saved = _read_json(scoring / "human_review.json")
                active_id = str(context["reviewer_id"])
                active_name = str(context["reviewer_name"])
                read_only = False
                notice = ""
                document = saved if saved is not None else questionnaire
                existing_id, existing_name = _review_owner(saved)
                if existing_id and existing_id != active_id:
                    read_only = True
                    notice = (
                        f"This review belongs to {existing_id}"
                        + (f" — {existing_name}" if existing_name else "")
                        + ". It is opened read-only; another reviewer cannot overwrite it."
                    )
                elif existing_id == active_id and existing_name and existing_name != active_name:
                    read_only = True
                    notice = (
                        f"Reviewer ID {active_id} is associated with {existing_name}. "
                        "The supplied reviewer name does not match, so this review is read-only."
                    )
                display_id = existing_id if read_only and existing_id else active_id
                display_name = existing_name if read_only and existing_name else active_name
                html = _html_document(
                    document,
                    reviewer_identity={"reviewer_id": display_id, "reviewer_name": display_name},
                    save_endpoint=f"/save/{token}",
                    read_only=read_only,
                    ownership_notice=notice,
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(html)))
                self.end_headers()
                self.wfile.write(html)

            def do_POST(self) -> None:
                token, context = self._context("/save/")
                if not token or context is None:
                    self._json(404, {"error": "Unknown review session."})
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = 0
                if length <= 0 or length > 8_000_000:
                    self._json(400, {"error": "Invalid review payload."})
                    return
                try:
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                except Exception:
                    self._json(400, {"error": "The review payload is not valid JSON."})
                    return
                if not isinstance(payload, dict):
                    self._json(400, {"error": "The review payload must be a JSON object."})
                    return

                active_id = str(context["reviewer_id"]).strip()
                active_name = str(context["reviewer_name"]).strip()
                reviewer = payload.get("reviewer", {}) or {}
                payload_id = str(reviewer.get("reviewer_id") or "").strip()
                payload_name = str(reviewer.get("reviewer_name") or "").strip()
                if not active_id or not active_name:
                    self._json(400, {"error": "Reviewer ID and Reviewer Name are required."})
                    return
                if payload_id != active_id or payload_name != active_name:
                    self._json(409, {"error": "Reviewer identity changed after the questionnaire was opened. Save is blocked."})
                    return
                registry_error = service._identity_error(active_id, active_name)
                if registry_error:
                    self._json(409, {"error": registry_error})
                    return

                scoring = Path(context["scoring_directory"])
                questionnaire = _read_json(scoring / "human_review_questionnaire.json")
                if not questionnaire or _is_baseline_questionnaire(questionnaire):
                    self._json(400, {"error": "This is not a reviewable experimental LLM questionnaire."})
                    return
                existing_path = scoring / "human_review.json"
                existing = _read_json(existing_path) if existing_path.is_file() else None
                existing_id, existing_name = _review_owner(existing)
                if existing_id and existing_id != active_id:
                    self._json(409, {"error": f"Review belongs to {existing_id}; overwrite is blocked."})
                    return
                if existing_id == active_id and existing_name and existing_name != active_name:
                    self._json(409, {"error": f"Reviewer ID {active_id} is associated with {existing_name!r}; overwrite is blocked."})
                    return

                payload.setdefault("reviewer", {})["reviewer_id"] = active_id
                payload["reviewer"]["reviewer_name"] = active_name
                payload["reviewer"]["reviewed_at_utc"] = datetime.now(timezone.utc).isoformat()
                temporary = existing_path.with_name(existing_path.name + ".tmp")
                try:
                    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                    temporary.replace(existing_path)
                    adjudicate_files(scoring)
                except Exception as exc:
                    try:
                        temporary.unlink(missing_ok=True)
                    except Exception:
                        pass
                    self._json(500, {"error": f"Review could not be saved: {exc}"})
                    return

                service.registry[active_id] = active_name
                state, completed, total = _review_completion(payload)
                self._json(200, {
                    "ok": True,
                    "state": state,
                    "criteria_completed": completed,
                    "criteria_total": total,
                    "message": f"Review saved. Rubric criteria completed: {completed}/{total}.",
                })

        return Handler


def launch_review_dashboard(parents: Iterable[Path] | Path) -> bool:
    """Launch the LLM-only Human Review launcher/status manager.

    The verbose HTML questionnaire is the single authoritative evaluation form.
    The Tk window manages dataset/algorithm selection and reviewer identity only.
    """
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    datasets = discover_review_datasets(parents)
    if not datasets:
        root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
        messagebox.showinfo(
            "No reviewable LLM algorithms",
            "No LLM human-review questionnaires were found.\n\n"
            "Human review applies only to experimental LLM result folders. "
            "Baseline algorithms do not require human review.",
            parent=root,
        )
        root.destroy()
        return False

    registry, registry_conflicts = reviewer_registry([Path(item["root"]) for item in datasets])
    service = _LocalReviewService(registry)

    root = tk.Tk()
    root.title("NL-FDEP Human Review")
    root.geometry("980x720")
    root.minsize(820, 620)

    top = ttk.LabelFrame(root, text="Review session")
    top.pack(fill="x", padx=12, pady=(12, 6))

    dataset_var = tk.StringVar()
    dataset_combo = ttk.Combobox(top, textvariable=dataset_var, state="readonly", width=42)
    dataset_combo.grid(row=0, column=1, padx=6, pady=6, sticky="w")
    ttk.Label(top, text="AI agent dataset").grid(row=0, column=0, padx=6, pady=6, sticky="w")
    add_dataset_button = ttk.Button(top, text="Add LLM dataset")
    add_dataset_button.grid(row=0, column=2, padx=6, pady=6)

    reviewer_id_var = tk.StringVar(value=next_reviewer_id(registry))
    reviewer_name_var = tk.StringVar(value="")
    ttk.Label(top, text="Reviewer ID").grid(row=1, column=0, padx=6, pady=6, sticky="w")
    reviewer_combo = ttk.Combobox(top, textvariable=reviewer_id_var, width=18)
    reviewer_combo.grid(row=1, column=1, padx=6, pady=6, sticky="w")
    ttk.Label(top, text="Reviewer Name").grid(row=2, column=0, padx=6, pady=6, sticky="w")
    reviewer_name_entry = ttk.Entry(top, textvariable=reviewer_name_var, width=44)
    reviewer_name_entry.grid(row=2, column=1, padx=6, pady=6, sticky="w")
    new_reviewer_button = ttk.Button(top, text="New reviewer")
    new_reviewer_button.grid(row=2, column=2, padx=6, pady=6)
    ttk.Label(
        top,
        text="Reviewer ID and name are associated study-wide and carried into every questionnaire opened in this session.",
        wraplength=720,
    ).grid(row=3, column=0, columnspan=3, padx=6, pady=(2, 8), sticky="w")
    top.columnconfigure(1, weight=1)

    if registry_conflicts:
        messagebox.showwarning(
            "Reviewer registry conflict",
            "Existing review files contain conflicting reviewer ID/name associations:\n\n"
            + "\n".join(registry_conflicts[:10])
            + "\n\nResolve these files before saving new reviews with the affected IDs.",
            parent=root,
        )

    body = tk.PanedWindow(root, orient="horizontal", sashwidth=6)
    body.pack(fill="both", expand=True, padx=12, pady=6)
    left = ttk.Frame(body)
    right = ttk.Frame(body)
    body.add(left, minsize=330)
    body.add(right, stretch="always")

    ttk.Label(left, text="Algorithms", font=("Arial", 11, "bold")).pack(anchor="w")
    lb = tk.Listbox(left, exportselection=False, width=46)
    lb.pack(fill="both", expand=True, pady=(5, 0))

    detail_title = ttk.Label(right, text="Select an algorithm", font=("Arial", 13, "bold"))
    detail_title.pack(anchor="w", pady=(0, 8))
    detail_text = tk.Text(right, height=18, wrap="word", state="disabled")
    detail_text.pack(fill="both", expand=True)
    actions = ttk.Frame(right)
    actions.pack(fill="x", pady=(10, 0))
    open_button = ttk.Button(actions, text="Open Questionnaire", state="disabled")
    open_button.pack(side="left")
    refresh_button = ttk.Button(actions, text="Refresh Review Status")
    refresh_button.pack(side="left", padx=8)
    end_session_button = ttk.Button(actions, text="End Review Session")
    end_session_button.pack(side="right")

    summary_var = tk.StringVar(value="")
    ttk.Label(root, textvariable=summary_var).pack(fill="x", padx=12, pady=(0, 12))

    state: dict[str, Any] = {"dataset_index": 0, "rows": datasets[0]["rows"]}

    def dataset_labels() -> list[str]:
        labels: list[str] = []
        used: dict[str, int] = {}
        for ds in datasets:
            base = ds["name"] or "Unnamed dataset"
            used[base] = used.get(base, 0) + 1
            labels.append(base if used[base] == 1 else f"{base} ({used[base]})")
        return labels

    def refresh_reviewer_controls() -> None:
        nonlocal registry
        registry, conflicts = reviewer_registry([Path(item["root"]) for item in datasets])
        service.registry = dict(registry)
        current = reviewer_id_var.get().strip()
        generated = next_reviewer_id(registry)
        values = sorted(registry, key=str.casefold)
        if generated not in values:
            values.append(generated)
        reviewer_combo["values"] = values
        if current in registry and registry[current]:
            reviewer_name_var.set(registry[current])
        if conflicts:
            summary_var.set("Reviewer registry contains conflicts; affected IDs cannot be safely reused until corrected.")

    def reviewer_changed(*_) -> None:
        reviewer_id = reviewer_id_var.get().strip()
        known = registry.get(reviewer_id)
        if known:
            reviewer_name_var.set(known)

    def new_reviewer() -> None:
        reviewer_id_var.set(next_reviewer_id(registry))
        reviewer_name_var.set("")
        reviewer_name_entry.focus_set()

    def set_detail(text: str) -> None:
        detail_text.config(state="normal")
        detail_text.delete("1.0", "end")
        detail_text.insert("1.0", text)
        detail_text.config(state="disabled")

    def row_label(row: dict[str, Any]) -> str:
        state_name = row.get("review_state") or "NOT_REVIEWED"
        if state_name == "COMPLETE":
            status = "Complete"
        elif state_name == "IN_PROGRESS":
            status = f"In progress {row.get('criteria_completed', 0)}/{row.get('criteria_total', 16)}"
        else:
            status = "Pending"
        owner = row.get("reviewer_id") or ""
        name = row.get("reviewer_name") or ""
        owner_text = f" · {owner}" if owner else ""
        if name:
            owner_text += f" — {name}"
        return f"Algorithm {row['algorithm_id']:>2}  · {status}{owner_text}"

    def update_algorithm_list(*_) -> None:
        idx = dataset_combo.current()
        if idx < 0:
            idx = 0
        state["dataset_index"] = idx
        rows = datasets[idx]["rows"]
        state["rows"] = rows
        lb.delete(0, "end")
        for row in rows:
            lb.insert("end", row_label(row))
        complete = sum(1 for row in rows if row.get("review_state") == "COMPLETE")
        in_progress = sum(1 for row in rows if row.get("review_state") == "IN_PROGRESS")
        summary_var.set(
            f"{datasets[idx]['name']}: {len(rows)} algorithms · {complete} complete · "
            f"{in_progress} in progress · {len(rows)-complete-in_progress} pending"
        )
        detail_title.config(text="Select an algorithm")
        set_detail("")
        open_button.config(state="disabled")

    def select_algorithm(_=None) -> None:
        if not lb.curselection():
            return
        row = state["rows"][lb.curselection()[0]]
        detail_title.config(text=f"Algorithm {row['algorithm_id']} · {datasets[state['dataset_index']]['name']}")
        owner = row.get("reviewer_id") or "None"
        owner_name = row.get("reviewer_name") or ""
        owner_line = owner + (f" — {owner_name}" if owner_name else "")
        set_detail(
            f"Review status: {row.get('review_state')}\n"
            f"Rubric criteria completed: {row.get('criteria_completed', 0)}/{row.get('criteria_total', 16)}\n"
            f"Review owner: {owner_line}\n\n"
            f"Scoring folder:\n{row['scoring_directory']}\n\n"
            "The HTML questionnaire is the authoritative human-evaluation form. "
            "Reviewer ID and Reviewer Name are populated from this launcher."
        )
        open_button.config(state="normal")

    def validate_identity() -> tuple[str, str] | None:
        reviewer_id = reviewer_id_var.get().strip()
        reviewer_name = reviewer_name_var.get().strip()
        if not reviewer_id or not reviewer_name:
            messagebox.showerror(
                "Reviewer identity required",
                "Enter both Reviewer ID and Reviewer Name before opening a questionnaire.",
                parent=root,
            )
            return None
        known = registry.get(reviewer_id)
        if known and known != reviewer_name:
            messagebox.showerror(
                "Reviewer ID/name mismatch",
                f"Reviewer ID {reviewer_id} is already associated with {known!r}.\n\n"
                "Use the associated name or select a new Reviewer ID.",
                parent=root,
            )
            return None
        return reviewer_id, reviewer_name

    def open_questionnaire() -> None:
        identity = validate_identity()
        if identity is None or not lb.curselection():
            return
        row = state["rows"][lb.curselection()[0]]
        reviewer_id, reviewer_name = identity
        url = service.register(Path(row["scoring_directory"]), reviewer_id, reviewer_name)
        webbrowser.open(url)

    def refresh_status() -> None:
        selected_dataset = state.get("dataset_index", 0)
        selected_algorithm = None
        if lb.curselection():
            selected_algorithm = state["rows"][lb.curselection()[0]].get("algorithm_id")
        for dataset in datasets:
            dataset["rows"] = review_status(Path(dataset["root"]))
        refresh_reviewer_controls()
        dataset_combo.current(min(selected_dataset, len(datasets)-1))
        update_algorithm_list()
        if selected_algorithm is not None:
            for index, row in enumerate(state["rows"]):
                if row.get("algorithm_id") == selected_algorithm:
                    lb.selection_set(index)
                    lb.see(index)
                    select_algorithm()
                    break

    def add_llm_dataset() -> None:
        selected = filedialog.askdirectory(title="Select an additional LLM dataset or Results folder", parent=root)
        if not selected:
            return
        additions = discover_review_datasets([Path(selected)])
        if not additions:
            messagebox.showinfo(
                "No reviewable LLM algorithms",
                "The selected folder contains no reviewable experimental LLM questionnaires. "
                "Baseline datasets are not eligible for Human Review.",
                parent=root,
            )
            return
        existing = {str(Path(item["root"]).resolve()).casefold() for item in datasets}
        added = None
        for item in additions:
            key = str(Path(item["root"]).resolve()).casefold()
            if key in existing:
                continue
            datasets.append(item)
            existing.add(key)
            added = len(datasets) - 1
        if added is None:
            messagebox.showinfo("Dataset already loaded", "That LLM dataset is already present in this Human Review session.", parent=root)
            return
        dataset_combo["values"] = dataset_labels()
        dataset_combo.current(added)
        refresh_reviewer_controls()
        update_algorithm_list()

    def close_review() -> None:
        # The browser questionnaire saves through this process-local HTTP service.
        # Accidentally closing the launcher used to terminate that service and left
        # still-open questionnaires with the browser-level error
        # "TypeError: Failed to fetch".  Once a questionnaire has been opened,
        # the window-manager close action therefore minimises the launcher instead.
        # The explicit End Review Session button remains the deliberate shutdown path.
        if service.contexts:
            root.iconify()
            return
        service.stop()
        root.destroy()

    def end_review_session() -> None:
        if service.contexts:
            confirmed = messagebox.askyesno(
                "End Human Review session",
                "Ending this session stops direct saving for any questionnaire tabs that are still open.\n\n"
                "Finish and save those reviews first, or choose Yes to end the session now.",
                parent=root,
            )
            if not confirmed:
                return
        service.stop()
        root.destroy()

    dataset_combo["values"] = dataset_labels()
    dataset_combo.current(0)
    reviewer_combo.bind("<<ComboboxSelected>>", reviewer_changed)
    reviewer_combo.bind("<FocusOut>", reviewer_changed)
    dataset_combo.bind("<<ComboboxSelected>>", update_algorithm_list)
    lb.bind("<<ListboxSelect>>", select_algorithm)
    add_dataset_button.config(command=add_llm_dataset)
    new_reviewer_button.config(command=new_reviewer)
    open_button.config(command=open_questionnaire)
    refresh_button.config(command=refresh_status)
    end_session_button.config(command=end_review_session)
    root.protocol("WM_DELETE_WINDOW", close_review)
    refresh_reviewer_controls()
    update_algorithm_list()
    root.mainloop()
    return True
