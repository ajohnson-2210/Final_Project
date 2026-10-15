"""Interactive PyCharm entry point for the controlled NL-FDEP routes."""

from __future__ import annotations

import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
COMPONENT_DIRECTORIES = [
    PROJECT_ROOT / 'parser components',
    PROJECT_ROOT / 'compiler components',
    PROJECT_ROOT / 'flow diagram components',
    PROJECT_ROOT / 'pipeline components',
    PROJECT_ROOT / 'study components',
    PROJECT_ROOT / 'cli components',
]
for component_directory in reversed(COMPONENT_DIRECTORIES):
    component_path = str(component_directory)
    if component_path not in sys.path:
        sys.path.insert(0, component_path)

from aj_test_harness import TestCase
from common_test_resources import DEFAULT_COMMON_TESTS_ROOT, TEST_DESIGN_VERSION, validate_common_test_pack
from flow_input_pipeline import DrawIOFlowInputPipeline
from input_selection import (
    BaselineStartupAction,
    HumanReviewStartupAction,
    InputRoute,
    InputSelectionCancelledError,
    InputSelectionDialog,
    PostLLMAction,
)
from nl_flow_pipeline import NLFlowDiagramEncoderPipeline
from pseudocode_profiles import PseudocodeProfile
from study_batch import StudyBatchProcessor, discover_algorithm_folders
from study_provenance import baseline_algorithm_design, validate_baseline
from study_review import (
    discover_sibling_review_roots,
    launch_review_dashboard,
    previous_study_review_roots,
    remember_review_study,
)
from study_rubric import PIPELINE_VERSION


OUTPUT_DIRECTORY = Path("output")
OPEN_VISUALISATIONS = True
BASELINE_REQUIRED_ROUTES = {InputRoute.LLM_RESULTS_FOLDER}
BASELINE_CALIBRATION_PROFILE = PseudocodeProfile.AJ_DIALECT_STRICT
TERMINAL_BASELINE_STATUSES = {"SUCCESS", "FAILURE", "EXPECTED_FAILURE", "REVIEW_REQUIRED"}
# v4.37 changes visualisation/review orchestration only; the parser, compiler and
# semantic pipeline are unchanged from v4.36.  A v4.36 baseline therefore remains
# a valid readiness-gate calibration in v4.37 and must not be recalibrated merely
# because the package version string changed.
BASELINE_SEMANTICALLY_COMPATIBLE_PIPELINE_VERSIONS = frozenset({"4.36", PIPELINE_VERSION})
RUNNER_STATE_SCHEMA_VERSION = "1.1"
RUNNER_STATE_PURPOSE = "SESSION_CRASH_RECOVERY_HINT"
RUNNER_STATE_FILE_ENV = "NL_FDEP_RUNNER_STATE_FILE"


def _runner_state_path() -> Path:
    """Return the per-user path for the temporary baseline recovery hint.

    The file deliberately lives outside the checksummed release tree so an
    unexpectedly terminated runner can expose the last established baseline as an
    explicit recovery hint on the next launch.  Orderly runner exits delete it.
    Tests and managed environments can override the location with
    ``NL_FDEP_RUNNER_STATE_FILE``.
    """
    override = os.environ.get(RUNNER_STATE_FILE_ENV)
    if override:
        return Path(override).expanduser()

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "NL-FDEP" / "runner_state.json"

    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home) / "NL-FDEP" / "runner_state.json"

    return Path.home() / ".config" / "NL-FDEP" / "runner_state.json"


def _load_runner_state() -> dict:
    path = _runner_state_path()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _saved_baseline_root() -> Path | None:
    value = _load_runner_state().get("last_baseline_root")
    if not isinstance(value, str) or not value.strip():
        return None
    return Path(value).expanduser()


def _save_baseline_preference(baseline_root: Path) -> None:
    """Write a temporary crash-recovery hint for the active session baseline.

    The historical function name is retained for regression compatibility.  The
    file is not a durable preference: orderly runner exits delete it, and any hint
    found at startup must still be explicitly accepted and fully revalidated.
    """
    path = _runner_state_path()
    payload = {
        "schema_version": RUNNER_STATE_SCHEMA_VERSION,
        "state_purpose": RUNNER_STATE_PURPOSE,
        "last_baseline_root": str(Path(baseline_root).resolve()),
        "last_selected_pipeline_version": PIPELINE_VERSION,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    except OSError as error:
        # Recovery-hint persistence is a convenience feature, not a reason to fail a run.
        print(f"WARNING: Could not save baseline recovery hint: {error}")


def _clear_baseline_preference() -> None:
    path = _runner_state_path()
    try:
        path.unlink(missing_ok=True)
    except OSError as error:
        print(f"WARNING: Could not clear baseline recovery hint: {error}")


TEST_CASES = [
    TestCase(
        name="Pipeline test",
        standard_input=[],
        expected_output=["6", "6"],
        timeout_seconds=3.0,
    )
]


def _requirement_distribution_names(requirements_file: Path) -> list[str]:
    """Return installable distribution names declared by a simple requirements file."""
    names: list[str] = []
    try:
        lines = Path(requirements_file).read_text(encoding="utf-8").splitlines()
    except OSError:
        return names
    for raw_line in lines:
        line = raw_line.split("#", 1)[0].strip()
        if not line or line.startswith(("-", "http://", "https://", "git+")):
            continue
        match = re.match(r"([A-Za-z0-9_.-]+)", line)
        if match:
            names.append(match.group(1))
    return names


def _missing_requirement_distributions(requirements_file: Path) -> list[str]:
    missing: list[str] = []
    for distribution in _requirement_distribution_names(requirements_file):
        try:
            importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            missing.append(distribution)
    return missing


def _install_requirements_file(requirements_file: Path, label: str) -> bool:
    """Install one requirements file using the exact Python interpreter running NL-FDEP."""
    requirements_file = Path(requirements_file)
    print(f"Installing {label} from {requirements_file.name}...", flush=True)
    completed = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if completed.returncode == 0:
        print(f"{label.capitalize()} installation complete.", flush=True)
        return True
    print(
        f"ERROR: {label.capitalize()} installation failed with exit code {completed.returncode}.",
        flush=True,
    )
    return False


def ensure_runner_dependencies(selection_dialog: InputSelectionDialog) -> bool:
    """Verify core then optional dependencies, installing missing packages with consent.

    The active interpreter (normally the user's .venv) is always used.  Core and
    optional requirement files are processed in that order.  Baseline/LLM study
    routes call this once per runner process before calibration or experimental work.
    """
    requirement_files = [
        (PROJECT_ROOT / "requirements.txt", "core dependencies"),
        (PROJECT_ROOT / "requirements-optional.txt", "optional benchmark dependencies"),
    ]
    missing_by_file: list[tuple[Path, str, list[str]]] = []
    for path, label in requirement_files:
        if not path.is_file():
            selection_dialog.show_error(
                "Dependency file missing",
                f"Required environment file was not found:\n\n{path}",
            )
            return False
        missing = _missing_requirement_distributions(path)
        if missing:
            missing_by_file.append((path, label, missing))

    if not missing_by_file:
        print(
            "Dependency verification: requirements.txt and requirements-optional.txt are satisfied "+
            f"in {sys.executable}",
            flush=True,
        )
        return True

    lines = [
        "NL-FDEP detected missing packages in the active Python environment:",
        "",
    ]
    for path, label, missing in missing_by_file:
        lines.append(f"{path.name} ({label}): {', '.join(missing)}")
    lines.extend([
        "",
        f"Python environment: {sys.executable}",
        "",
        "Install the missing requirements now? Core requirements will be processed first, "+
        "followed by optional benchmark requirements.",
    ])
    if not selection_dialog.ask_yes_no("Install NL-FDEP dependencies", "\n".join(lines)):
        return False

    # Process both files in the documented order when installation is needed.
    for path, label in requirement_files:
        if not _install_requirements_file(path, label):
            selection_dialog.show_error(
                "Dependency installation failed",
                f"NL-FDEP could not install {label} from {path.name}.\n\n"
                f"Active Python: {sys.executable}\n\n"
                "Baseline calibration and LLM study processing have not started.",
            )
            return False

    remaining = []
    for path, label in requirement_files:
        missing = _missing_requirement_distributions(path)
        if missing:
            remaining.append(f"{path.name}: {', '.join(missing)}")
    if remaining:
        selection_dialog.show_error(
            "Dependency verification failed",
            "Installation completed but these packages are still unavailable:\n\n"
            + "\n".join(remaining),
        )
        return False

    print("Dependency verification complete: core and optional requirements are available.", flush=True)
    return True


def run_pseudocode_pipeline(input_path: Path, pseudocode_profile: PseudocodeProfile):
    """Run the canonical pipeline using a selected AJ pseudocode file."""
    pseudocode = input_path.read_text(encoding="utf-8")
    return NLFlowDiagramEncoderPipeline().run(
        pseudocode=pseudocode,
        output_directory=OUTPUT_DIRECTORY,
        test_cases=TEST_CASES,
        open_visualisations=OPEN_VISUALISATIONS,
        pseudocode_profile=pseudocode_profile,
    )


def run_flow_diagram_pipeline(input_path: Path):
    """Run the controlled draw.io import route."""
    return DrawIOFlowInputPipeline().run(
        input_path=input_path,
        output_directory=OUTPUT_DIRECTORY,
        test_cases=[],
        open_visualisations=OPEN_VISUALISATIONS,
    )


def run_llm_results_folder(
    input_path: Path,
    pseudocode_profile: PseudocodeProfile,
):
    """Batch-process Algorithm - n folders using frozen static semantic expectations.

    The procedural baseline-readiness gate is enforced by ``main`` before this
    function is called.  The baseline path is deliberately not accepted here, so
    experimental scoring cannot consult the benchmark at runtime.
    """
    return StudyBatchProcessor().process_llm_results(
        results_directory=input_path,
        profile=pseudocode_profile,
        baseline_root=None,
        open_visualisations=False,
    )


def run_baseline_folder(input_path: Path, pseudocode_profile: PseudocodeProfile):
    """Process a runtime-selected baseline using the packaged Common Test design."""
    return StudyBatchProcessor().process_baseline(
        baseline_root=input_path,
        profile=pseudocode_profile,
        open_visualisations=False,
    )


def run_human_review_folder(
    input_path: Path | list[Path],
    *,
    discover_siblings: bool = False,
    regenerate_dashboards: bool = False,
):
    """Launch the integrated LLM-only review dashboard for one or more datasets.

    Standalone Human Review can optionally reconstruct a cross-session registry by
    discovering sibling completed LLM datasets. Same-session review passes its
    explicit in-memory registry and leaves ``discover_siblings`` disabled.
    """
    roots = [Path(value) for value in input_path] if isinstance(input_path, list) else [Path(input_path)]
    if discover_siblings and len(roots) == 1:
        discovered = discover_sibling_review_roots(roots[0])
        if discovered:
            roots = discovered
        print(
            f"Human Review discovery: {len(roots)} completed experimental LLM dataset(s) available.",
            flush=True,
        )
    else:
        print(
            f"Human Review start fresh/current session: {len(roots)} LLM dataset(s) loaded.",
            flush=True,
        )

    # Human Review can be opened directly from previously processed LLM folders,
    # bypassing process_llm_results(). Refresh only stale experimental DrawIO
    # views here so silent v4.37 routing fixes are visible without touching any
    # semantic/scoring/review artefact. Baselines are explicitly ignored by the
    # refresh helper.
    drawio_refreshed = 0
    drawio_errors: list[str] = []
    refresher = StudyBatchProcessor()
    for root in roots:
        refresh = refresher.refresh_llm_drawio_views(root)
        drawio_refreshed += int(refresh.get("refreshed", 0))
        drawio_errors.extend(refresh.get("errors", []))
    if drawio_refreshed:
        print(
            f"Human Review visual refresh: {drawio_refreshed} stale DrawIO file(s) updated.",
            flush=True,
        )
    if drawio_errors:
        print(
            "Human Review visual refresh warnings: " + "; ".join(drawio_errors),
            flush=True,
        )

    if regenerate_dashboards and roots:
        try:
            from dashboard_generation import infer_study_root, regenerate_study_dashboards
            study_root = infer_study_root(roots[0], "LLM_RESULTS")
            if study_root is not None and study_root.is_dir():
                dashboard_status = regenerate_study_dashboards(study_root)
                print(
                    "Human Review dashboard refresh: "
                    f"{len(dashboard_status.get('individual_dashboards') or [])} individual, "
                    "comparative heat map, comparative radial, all-agent radial profiles, final scoring, "
                    "and combined human-review dashboards generated.",
                    flush=True,
                )
                if int(dashboard_status.get("dataset_mismatch_count") or 0):
                    print(
                        "WARNING: Human Review recovered a study with LLM dataset algorithm-count/ID mismatches. "
                        f"Expected N={dashboard_status.get('expected_algorithm_count')}; "
                        f"mismatched dataset(s)={dashboard_status.get('dataset_mismatch_count')}. "
                        f"Audit: {dashboard_status.get('dataset_consistency_file')}",
                        flush=True,
                    )
        except Exception as exc:
            print(
                f"Human Review dashboard refresh warning: {type(exc).__name__}: {exc}",
                flush=True,
            )

    opened = launch_review_dashboard(roots)
    return {
        "status": "REVIEW_SESSION_CLOSED" if opened else "NO_REVIEWABLE_LLM_DATASETS",
        "review_roots": [str(value.resolve()) for value in roots],
        "discovery_mode": "DISCOVER_SIBLINGS" if discover_siblings else "EXPLICIT_ONLY",
    }


def _normalise_llm_results_directory(selected_path: Path) -> Path | None:
    """Resolve a user-selected LLM root to the directory containing Algorithm - n folders.

    Accepted layouts are either::

        selected_root/Algorithm - 1/...

    or::

        selected_root/results/Algorithm - 1/...

    The second form matches the study export layout used by the LLM result sets.
    """
    selected_path = Path(selected_path)
    if not selected_path.is_dir():
        return None

    if discover_algorithm_folders(selected_path):
        return selected_path

    results_children = [
        child for child in selected_path.iterdir()
        if child.is_dir() and child.name.casefold() == "results"
    ]
    if len(results_children) == 1 and discover_algorithm_folders(results_children[0]):
        return results_children[0]

    return None


def select_llm_results_directory(
    selection_dialog: InputSelectionDialog,
    baseline_root: Path | None = None,
) -> Path:
    """Prompt explicitly for the experimental LLM dataset.

    v4.37 experimental scoring is baseline-independent.  ``baseline_root`` is
    the already validated procedural readiness-gate path and is used here only
    to prevent accidentally selecting the benchmark itself as the experimental
    dataset.  It is never used to generate or score expected results. Invalid selections are explained and
    re-prompted until the user selects a usable LLM root or cancels the chooser.
    """
    selection_dialog.show_info(
        "Select LLM results dataset",
        "Select the LLM results dataset. You may select either:\n"
        "- the folder that directly contains 'Algorithm - 1' ... 'Algorithm - 50'; or\n"
        "- its parent folder when the Algorithm folders are inside a child folder named 'results'.",
    )

    baseline_resolved = Path(baseline_root).resolve() if baseline_root is not None else None
    while True:
        selected_path = selection_dialog.select_file(route=InputRoute.LLM_RESULTS_FOLDER)
        selected_resolved = Path(selected_path).resolve()

        if baseline_resolved is not None and selected_resolved == baseline_resolved:
            selection_dialog.show_error(
                "LLM results folder required",
                "The Baseline benchmark folder cannot also be used as the LLM results folder.\n\n"
                "Please select the experimental LLM dataset instead.",
            )
            continue

        normalised = _normalise_llm_results_directory(selected_path)
        if normalised is None:
            selection_dialog.show_error(
                "LLM results folder not recognised",
                "No 'Algorithm - n' folders were found in the selected directory.\n\n"
                "Select either the directory that directly contains the Algorithm folders, "
                "or their parent directory when they are inside a child folder named 'results'.",
            )
            continue

        if baseline_resolved is not None and normalised.resolve() == baseline_resolved:
            selection_dialog.show_error(
                "LLM results folder required",
                "The resolved LLM results directory is the Baseline benchmark folder.\n\n"
                "Please select the experimental LLM dataset instead.",
            )
            continue

        return normalised


def _read_json(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def _current_baseline_state(baseline_root: Path, expected_ids=None) -> dict:
    """Summarise current baseline outcomes using the independent Baseline count B."""
    design = baseline_algorithm_design(baseline_root)
    if expected_ids is None:
        expected_ids = design.get("expected_algorithm_ids") or []
    expected_ids = list(expected_ids)
    state = {
        "required_count": len(expected_ids),
        "expected_algorithm_ids": expected_ids,
        "baseline_design_status": design.get("status"),
        "baseline_design": design,
        "terminal": 0,
        "evaluated": 0,
        "full_score": 0,
        "pipeline_success": 0,
        "pipeline_failure": 0,
        "behavioural_not_evaluated": 0,
        "other_unavailable": 0,
    }
    for algorithm_id in expected_ids:
        artifact_directory = (
            Path(baseline_root)
            / "pseudocode"
            / f"Algorithm - {algorithm_id}"
            / "pipeline_artifacts"
        )
        manifest = _read_json(artifact_directory / "manifest.json") or {}
        calibration = (
            _read_json(artifact_directory / "baseline_calibration.json")
            or _read_json(artifact_directory / "baseline_python_comparison.json")
            or {}
        )
        if not (
            manifest.get("pipeline_version") in BASELINE_SEMANTICALLY_COMPATIBLE_PIPELINE_VERSIONS
            and manifest.get("pseudocode_profile") == BASELINE_CALIBRATION_PROFILE.value
            and manifest.get("processing_status") in TERMINAL_BASELINE_STATUSES
        ):
            continue
        state["terminal"] += 1
        processing_status = manifest.get("processing_status")
        if processing_status == "SUCCESS":
            state["pipeline_success"] += 1

        if (
            calibration.get("status") == "EVALUATED"
            and calibration.get("calibration_score_percentage") is not None
        ):
            state["evaluated"] += 1
            try:
                score = float(calibration.get("calibration_score_percentage"))
            except (TypeError, ValueError):
                score = None
            if score is not None and abs(score - 100.0) <= 1e-9:
                state["full_score"] += 1
        elif processing_status == "FAILURE":
            state["pipeline_failure"] += 1
        elif processing_status == "SUCCESS":
            state["behavioural_not_evaluated"] += 1
        else:
            state["other_unavailable"] += 1
    return state


def _current_baseline_calibration_count(baseline_root: Path, expected_ids=None) -> int:
    """Count current evaluated calibration measurements."""
    return _current_baseline_state(baseline_root, expected_ids)["evaluated"]


def _baseline_required_count(state: dict) -> int:
    """Return Baseline B from current state, with legacy-state compatibility."""
    return int(
        state.get("required_count")
        or max(
            int(state.get("terminal", 0)),
            int(state.get("evaluated", 0)) + int(state.get("behavioural_not_evaluated", 0)),
            int(state.get("full_score", 0)),
        )
        or 0
    )


def _baseline_study_ready(state: dict) -> bool:
    """Return whether the benchmark satisfies the experimental readiness gate.

    Baseline readiness is evaluated against the independent Baseline denominator
    B, inferred from the submitted baseline folders.  All B algorithms must
    process successfully.  Every behaviourally evaluable calibration must score
    100%.  As in the existing v4.37 rule, at most one genuinely NOT_EVALUATED
    behavioural case may remain explicit rather than being assigned a score.
    """
    terminal = int(state.get("terminal", 0))
    evaluated = int(state.get("evaluated", 0))
    full_score = int(state.get("full_score", 0))
    pipeline_failure = int(state.get("pipeline_failure", 0))
    behavioural_not_evaluated = int(state.get("behavioural_not_evaluated", 0))
    other_unavailable = int(state.get("other_unavailable", 0))
    # Actual runner state always carries required_count.  The fallback keeps
    # older tests/callers compatible without reintroducing a fixed denominator.
    required = _baseline_required_count(state)
    pipeline_success = int(state.get("pipeline_success", terminal - pipeline_failure))
    design_status = state.get("baseline_design_status")
    return (
        required > 0
        and design_status in {None, "MATCH"}
        and terminal == required
        and pipeline_success == required
        and pipeline_failure == 0
        and other_unavailable == 0
        and evaluated in {max(0, required - 1), required}
        and full_score == evaluated
        and evaluated + behavioural_not_evaluated == required
    )


def _baseline_problem_summary(report: dict) -> str:
    rows = [row for row in report.get("algorithms", []) if row.get("status") != "READY"]
    examples = []
    for row in rows[:8]:
        issues = ", ".join(row.get("issues") or ["unknown issue"])
        examples.append(f"Algorithm {row.get('algorithm_id')}: {issues}")
    suffix = "" if len(rows) <= 8 else f"\n...and {len(rows) - 8} more algorithm issue(s)."
    return "\n".join(examples) + suffix


def _baseline_design_problem_summary(report: dict) -> str:
    """Human-readable Baseline B/ID integrity summary from preflight."""
    design = report.get("baseline_design") or {}
    if design.get("status") == "MATCH":
        return ""
    b = int(design.get("baseline_algorithm_count") or 0)
    lines = [
        f"Baseline count B: {b}",
        f"Expected baseline IDs: {'1–' + str(b) if b > 0 else 'none'}",
    ]
    for label, key in (
        ("Missing pseudocode IDs", "missing_pseudocode_algorithm_ids"),
        ("Missing reference-Python IDs", "missing_python_algorithm_ids"),
        ("Unexpected pseudocode IDs", "extra_pseudocode_algorithm_ids"),
        ("Unexpected reference-Python IDs", "extra_python_algorithm_ids"),
    ):
        values = design.get(key) or []
        if values:
            lines.append(f"{label}: " + ", ".join(str(x) for x in values))
    if design.get("issues"):
        lines.append("Integrity issues: " + ", ".join(str(x) for x in design.get("issues") or []))
    return "\n".join(lines)


def _baseline_calibration_problem_details(
    baseline_root: Path,
    report: dict | None = None,
    expected_ids=None,
) -> list[dict]:
    """Return current non-100%-calibrated algorithms with the best available reason.

    The latest baseline batch report is used for human-readable runtime errors (for
    example a missing optional dependency).  Current manifests/calibration files remain
    authoritative for deciding whether an algorithm is actually ready.
    """
    baseline_root = Path(baseline_root)
    if expected_ids is None:
        expected_ids = baseline_algorithm_design(baseline_root).get("expected_algorithm_ids") or []
    if report is None:
        report = _read_json(baseline_root / "study_analysis" / "batch_report.json") or {}
    report_rows = {
        int(row.get("algorithm_id")): row
        for row in report.get("algorithms", [])
        if isinstance(row, dict) and str(row.get("algorithm_id", "")).isdigit()
    }
    problems: list[dict] = []
    for algorithm_id in expected_ids:
        artifact_directory = (
            baseline_root / "pseudocode" / f"Algorithm - {algorithm_id}" / "pipeline_artifacts"
        )
        manifest = _read_json(artifact_directory / "manifest.json") or {}
        calibration = (
            _read_json(artifact_directory / "baseline_calibration.json")
            or _read_json(artifact_directory / "baseline_python_comparison.json")
            or {}
        )
        current_terminal = (
            manifest.get("pipeline_version") in BASELINE_SEMANTICALLY_COMPATIBLE_PIPELINE_VERSIONS
            and manifest.get("pseudocode_profile") == BASELINE_CALIBRATION_PROFILE.value
            and manifest.get("processing_status") in TERMINAL_BASELINE_STATUSES
        )
        score = calibration.get("calibration_score_percentage")
        try:
            numeric_score = float(score) if score is not None else None
        except (TypeError, ValueError):
            numeric_score = None
        fully_calibrated = (
            current_terminal
            and manifest.get("processing_status") == "SUCCESS"
            and calibration.get("status") == "EVALUATED"
            and numeric_score is not None
            and abs(numeric_score - 100.0) <= 1e-9
        )
        if fully_calibrated:
            continue

        row = report_rows.get(int(algorithm_id), {})
        pipeline_report = _read_json(artifact_directory / "pipeline_report.json") or {}
        if not current_terminal:
            category = "CURRENT_CALIBRATION_MISSING_OR_STALE"
        elif manifest.get("processing_status") != "SUCCESS":
            category = f"PIPELINE_{manifest.get('processing_status') or 'UNAVAILABLE'}"
        elif calibration.get("status") != "EVALUATED":
            category = str(calibration.get("status") or "BEHAVIOURAL_NOT_EVALUATED")
        elif numeric_score is not None and abs(numeric_score - 100.0) > 1e-9:
            category = "CALIBRATION_BELOW_100"
        else:
            category = "CALIBRATION_UNAVAILABLE"

        reason = (
            row.get("error")
            or pipeline_report.get("error")
            or calibration.get("reason")
        )
        if not reason and category == "CALIBRATION_BELOW_100":
            reason = f"Calibration score is {numeric_score:g}% rather than the required 100%."
        if not reason:
            reason = (
                f"processing_status={manifest.get('processing_status') or 'missing'}; "
                f"calibration_status={calibration.get('status') or 'missing'}"
            )
        problems.append({
            "algorithm_id": int(algorithm_id),
            "category": category,
            "reason": str(reason),
            "processing_status": manifest.get("processing_status"),
            "calibration_status": calibration.get("status"),
            "calibration_score_percentage": numeric_score,
        })
    return problems


def _format_baseline_calibration_problems(problems: list[dict], limit: int = 8) -> str:
    if not problems:
        return "No individual calibration problem could be identified."
    rows = []
    for problem in problems[:limit]:
        rows.append(
            f"Algorithm {problem.get('algorithm_id')}: {problem.get('category')}\n"
            f"Reason: {problem.get('reason')}"
        )
    if len(problems) > limit:
        rows.append(f"...and {len(problems) - limit} more calibration problem(s).")
    return "\n\n".join(rows)


def _baseline_session_ready(baseline_root: Path, state: dict | None = None) -> bool:
    """Return whether the active baseline still satisfies the single readiness gate."""
    state = state or _current_baseline_state(baseline_root)
    return _baseline_study_ready(state)


def ensure_baseline_available(
    selection_dialog: InputSelectionDialog,
    pseudocode_profile: PseudocodeProfile,
    baseline_root: Path | None = None,
    require_full_study_readiness: bool = False,
    persist_preference: bool = True,
    force_recalibration: bool = False,
) -> Path | None:
    """Obtain, validate and if necessary calibrate a baseline dependency.

    When ``require_full_study_readiness`` is true, the benchmark is a procedural
    gate only: all Baseline B algorithms must process successfully and every behaviourally
    evaluable calibration must score 100%. A genuinely NOT_EVALUATED behavioural
    case remains explicit and does not create a degraded readiness state. The
    baseline is never supplied to experimental scoring.

    Cancelling or declining returns ``None`` and the requested dependent
    operation is not started.
    """
    if baseline_root is None:
        if not selection_dialog.ask_yes_no(
            "Baseline benchmark required",
            "This operation requires a baseline benchmark.\n\n"
            "No ready benchmark has been discovered. Would you like to provide one now?",
        ):
            return None

        baseline_root = selection_dialog.select_optional_directory(
            "Select the Baseline benchmark folder containing pseudocode and python folders"
        )
        if baseline_root is None:
            return None
    else:
        baseline_root = Path(baseline_root)

    report = validate_baseline(
        baseline_root,
        common_tests_root=DEFAULT_COMMON_TESTS_ROOT,
    )
    if not report.get("baseline_root_structure_valid") or report.get("issue_count", 0):
        pack = report.get("common_test_pack") or {}
        pack_note = ""
        if not pack.get("complete"):
            pack_note = (
                f"\n\nPackaged Common Tests v{TEST_DESIGN_VERSION} are incomplete in this build. "
                "Baseline-local Tests.json files can be used only as a backward-compatible fallback."
            )
        design_note = _baseline_design_problem_summary(report)
        detail_parts = [part for part in (design_note, _baseline_problem_summary(report)) if part]
        selection_dialog.show_error(
            "Baseline benchmark is not ready",
            "The selected baseline did not pass preflight.\n\n"
            + ("\n\n".join(detail_parts) or "Required baseline structure was not found.")
            + pack_note,
        )
        return None

    state = _current_baseline_state(baseline_root)
    required = _baseline_required_count(state)
    calibration_needed = force_recalibration or (
        not _baseline_study_ready(state)
        if require_full_study_readiness
        else state["terminal"] < required
    )
    if calibration_needed:
        if require_full_study_readiness:
            readiness_detail = (
                f"Current NL-FDEP v{PIPELINE_VERSION} readiness:\n"
                f"- terminal calibration runs: {state['terminal']}/{required}\n"
                f"- pipeline failures: {state.get('pipeline_failure', 0)}\n"
                f"- behaviourally evaluated: {state['evaluated']}/{required}\n"
                f"- evaluable calibrations at 100%: {state.get('full_score', 0)}/{state['evaluated']}\n"
                f"- behaviourally not evaluated: {state.get('behavioural_not_evaluated', 0)}\n\n"
                f"Study readiness requires all {required} baseline algorithms (Baseline Algorithms 1–{required}) to process successfully "
                "and every behaviourally evaluable calibration to score 100%. Would you like "
                "to calibrate it now and then resume the selected LLM operation?"
            )
        else:
            readiness_detail = (
                f"The selected baseline has {state['terminal']}/{required} current NL-FDEP v{PIPELINE_VERSION} "
                "terminal calibration runs and "
                f"{state['evaluated']}/{required} evaluated behavioural calibrations.\n\n"
                "Would you like to calibrate it now and then continue with the selected operation?"
            )

        # Choosing the explicit "Choose baseline folder and recalibrate" action is
        # itself authorisation for the calibration; do not ask a redundant second
        # yes/no question.  Other stale/missing-currentness paths still require
        # the existing confirmation.
        if not force_recalibration and not selection_dialog.ask_yes_no(
            "Baseline calibration required",
            readiness_detail,
        ):
            return None
        calibration_result = run_baseline_folder(
            input_path=baseline_root,
            pseudocode_profile=BASELINE_CALIBRATION_PROFILE,
        )
        state = _current_baseline_state(baseline_root)
        required = _baseline_required_count(state)
        report_block = calibration_result.get("report", {})
        print("BASELINE CALIBRATION COMPLETE")
        print("=" * 52)
        print(f"Algorithms represented: {report_block.get('algorithm_count', 0)}")
        print(f"Calibration status counts: {report_block.get('calibration_status_counts', {})}")
        print(f"Evaluated behavioural calibrations: {state['evaluated']}/{required}")
        if require_full_study_readiness:
            print(f"100% calibration outcomes: {state.get('full_score', 0)}/{required}")

    if require_full_study_readiness and not _baseline_study_ready(state):
        problems = _baseline_calibration_problem_details(
            baseline_root,
            report=(calibration_result.get("report", {}) if calibration_needed else None),
        )
        detail = _format_baseline_calibration_problems(problems)
        selection_dialog.show_error(
            "Baseline calibration is not study-ready",
            "The selected benchmark does not satisfy the v4.37 experimental readiness gate.\n\n"
            f"Required: {required}/{required} pipeline-successful baseline algorithms (Baseline Algorithms 1–{required}) and every behaviourally "
            "evaluable calibration at 100%.\n"
            f"Current: {state['terminal']}/{required} terminal; "
            f"pipeline failures={state.get('pipeline_failure', 0)}; "
            f"{state['evaluated']}/{required} behaviourally evaluated; "
            f"{state.get('full_score', 0)}/{state['evaluated']} evaluable calibrations at 100%; "
            f"{state.get('behavioural_not_evaluated', 0)} behaviourally NOT_EVALUATED.\n\n"
            f"Calibration problem details:\n{detail}\n\n"
            "There is no degraded missing-baseline dependency override. Resolve any dependency or pipeline "
            "failure and recalibrate before starting an LLM study.",
        )
        return None
    elif state["evaluated"] < required:
        unavailable = required - state["evaluated"]
        if not selection_dialog.ask_yes_no(
            "Baseline calibration has limitations",
            f"The selected benchmark has {state['evaluated']}/{required} evaluated behavioural calibrations.\n\n"
            f"Unavailable for baseline-relative behavioural comparison: {unavailable}\n"
            f"- pipeline/structural failure: {state['pipeline_failure']}\n"
            f"- behavioural test not evaluable: {state['behavioural_not_evaluated']}\n"
            f"- other unavailable current outcomes: {state['other_unavailable']}\n\n"
            "You can continue. Algorithms without an eligible calibration will be reported as NOT_EVALUABLE "
            "for baseline-relative behavioural comparison rather than being assigned an invented score.\n\n"
            "Continue with the selected operation?",
        ):
            return None

    if persist_preference:
        _save_baseline_preference(baseline_root)
    return baseline_root


def establish_session_baseline(
    selection_dialog: InputSelectionDialog,
    pseudocode_profile: PseudocodeProfile,
) -> Path | None:
    """Establish one explicit study-ready baseline for the current LLM session.

    On the first LLM operation in a process, any runner-state file left by an
    unfinished or legacy session is treated only as a recovery hint.  If a previous
    benchmark is found, the user must explicitly choose whether to reuse it or choose
    a baseline folder and recalibrate.  If no previous benchmark is found, the user is
    directed straight to the baseline-folder chooser and the selected benchmark is
    calibrated when necessary.

    Once established, the baseline remains in memory for subsequent LLM folders in
    the same process.  It is a procedural readiness gate only and is never forwarded
    into experimental semantic scoring.
    """
    saved_root = _saved_baseline_root()

    if saved_root is not None:
        saved_root = Path(saved_root).expanduser()
        if not saved_root.is_dir():
            _clear_baseline_preference()
            selection_dialog.show_info(
                "Previously selected baseline unavailable",
                "A previously selected baseline was recorded, but the folder can no longer be found:\n\n"
                f"{saved_root}\n\n"
                "Select a baseline benchmark folder to establish the study-readiness gate.",
            )
            saved_root = None
        else:
            preflight = validate_baseline(saved_root, common_tests_root=DEFAULT_COMMON_TESTS_ROOT)
            if not preflight.get("baseline_root_structure_valid") or preflight.get("issue_count", 0):
                _clear_baseline_preference()
                selection_dialog.show_info(
                    "Previously selected baseline is no longer valid",
                    "A previous baseline folder was detected, but it no longer passes the current "
                    "baseline preflight:\n\n"
                    f"{saved_root}\n\n"
                    "Select a baseline benchmark folder to establish the study-readiness gate.",
                )
                saved_root = None

    if saved_root is not None:
        detected_state = _current_baseline_state(saved_root)
        action = selection_dialog.select_detected_baseline_action(
            saved_root,
            _baseline_study_ready(detected_state),
        )
        if action == BaselineStartupAction.QUIT:
            return None
        if action == BaselineStartupAction.USE_DETECTED_BASELINE:
            return ensure_baseline_available(
                selection_dialog,
                pseudocode_profile,
                baseline_root=saved_root,
                require_full_study_readiness=True,
                persist_preference=True,
            )
        if action != BaselineStartupAction.CHOOSE_AND_RECALIBRATE:
            raise ValueError(f"Unsupported baseline startup action: {action}")

        chosen_root = selection_dialog.select_optional_directory(
            "Select the Baseline benchmark folder to recalibrate"
        )
        if chosen_root is None:
            return None
        return ensure_baseline_available(
            selection_dialog,
            pseudocode_profile,
            baseline_root=chosen_root,
            require_full_study_readiness=True,
            persist_preference=True,
            force_recalibration=True,
        )

    selection_dialog.show_info(
        "Baseline benchmark required",
        "No previously selected baseline benchmark was detected.\n\n"
        "Select the trusted Baseline benchmark folder. It will be validated and, "
        "when necessary, calibrated before the LLM dataset is selected.",
    )
    chosen_root = selection_dialog.select_optional_directory(
        "Select the Baseline benchmark folder containing pseudocode and python folders"
    )
    if chosen_root is None:
        return None

    return ensure_baseline_available(
        selection_dialog,
        pseudocode_profile,
        baseline_root=chosen_root,
        require_full_study_readiness=True,
        persist_preference=True,
    )



def run_selected_pipeline(
    route: InputRoute,
    input_path: Path,
    pseudocode_profile: PseudocodeProfile | None = None,
    baseline_root: Path | None = None,
):
    """Route a selected source file/folder to its controlled pipeline."""
    if route == InputRoute.PSEUDOCODE:
        return run_pseudocode_pipeline(
            input_path=input_path,
            pseudocode_profile=pseudocode_profile or PseudocodeProfile.AJ_DIALECT_STRICT,
        )
    if route == InputRoute.FLOW_DIAGRAM:
        return run_flow_diagram_pipeline(input_path=input_path)
    if route == InputRoute.LLM_RESULTS_FOLDER:
        # The baseline has already served its procedural readiness-gate role in
        # ``main``.  Do not forward its path into experimental scoring.
        return run_llm_results_folder(
            input_path=input_path,
            pseudocode_profile=pseudocode_profile or PseudocodeProfile.GENERIC_COMPATIBILITY,
        )
    if route == InputRoute.BASELINE_BENCHMARK_FOLDER:
        return run_baseline_folder(
            input_path=input_path,
            pseudocode_profile=pseudocode_profile or PseudocodeProfile.GENERIC_COMPATIBILITY,
        )
    if route == InputRoute.HUMAN_REVIEW_FOLDER:
        return run_human_review_folder(input_path)
    raise ValueError(f"Unsupported input route: {route}")


def print_pipeline_report(result) -> None:
    """Print a concise pipeline report in the PyCharm console."""
    print("NL TO FLOW DIAGRAM ENCODER PIPELINE")
    print("=" * 52)
    for stage in result.stages:
        print(
            f"[{stage.status:7}] "
            f"{stage.name:<28} "
            f"{stage.duration_ms:>9.3f} ms  "
            f"{stage.message}"
        )
    print("\nOUTPUT FILES")
    for output_name, output_path in result.output_files.items():
        print(f"- {output_name}: {output_path}")
    if result.test_report is not None:
        print(
            "\nTests passed: "
            f"{result.test_report.passed_tests}/{len(result.test_report.results)}"
        )
    if not result.success:
        print(f"\nPipeline failed: {result.error or 'One or more tests failed.'}")


def _print_study_batch_result(
    selected_route: InputRoute,
    result: dict,
) -> None:
    """Print a study-batch summary for baseline or LLM processing."""
    report = result.get("report", {})
    print("STUDY BATCH COMPLETE")
    print("=" * 52)
    print(f"Dataset: {report.get('dataset')}")
    print(f"Algorithms represented: {report.get('algorithm_count', 0)}")
    print(f"Pipeline status counts: {report.get('pipeline_status_counts', report.get('status_counts', {}))}")
    if report.get('batch_type') == 'BASELINE':
        calibration_counts = report.get('calibration_status_counts', {}) or {}
        evaluated = int(report.get('evaluated_baseline_calibration_count') or 0)
        print(f"Baseline calibration counts: {calibration_counts}")
        print(f"Evaluated behavioural calibrations: {evaluated}/{report.get('algorithm_count', 0)}")
        print(f"Mean baseline calibration score: {report.get('mean_baseline_calibration_percentage')}")
        print("Note: pipeline FAILURE may represent measured behavioural disagreement; calibration availability is reported separately above.")
        structural_failures = int(calibration_counts.get('PIPELINE_FAILURE', 0))
        if structural_failures:
            print(f"WARNING: {structural_failures} algorithm(s) did not reach an evaluated baseline calibration.")
        unavailable = int(report.get('baseline_calibration_unavailable_count') or 0)
        if unavailable:
            print(
                f"Baseline-relative behavioural comparison is available for {evaluated}/{report.get('algorithm_count', 0)} algorithms; "
                f"the remaining {unavailable} will be reported as NOT_EVALUABLE if used experimentally."
            )
    elif report.get('batch_type') == 'LLM_RESULTS':
        print(f"Comparison to frozen semantic reference: {report.get('comparison_to_baseline_counts', {})}")
        print(f"Mean experimental semantic behavioural score: {report.get('mean_experimental_behavioural_percentage')}")
        print(f"Mean delta from frozen semantic reference (percentage points): {report.get('mean_delta_from_baseline_percentage_points')}")
        semantic_evaluable = int(report.get('semantic_tests_evaluable') or 0)
        semantic_passed = int(report.get('semantic_tests_passed') or 0)
        semantic_ne = int(report.get('semantic_tests_not_evaluable') or 0)
        if semantic_evaluable or semantic_ne:
            print(f"Task-semantic Common Tests: {semantic_passed}/{semantic_evaluable} passed; {semantic_ne} not evaluable/reference-only")
            print(f"Aggregate task-semantic test accuracy: {report.get('semantic_test_accuracy_percentage')}")
        boundary_evaluable = int(report.get('semantic_boundary_probes_evaluable') or 0)
        boundary_ne = int(report.get('semantic_boundary_probes_not_evaluable') or 0)
        if boundary_evaluable or boundary_ne:
            print(
                "Semantic boundary probes: "
                f"{report.get('semantic_boundary_probes_accepted', 0)} accepted out-of-domain / {boundary_evaluable} evaluable; "
                f"{report.get('semantic_boundary_probes_controlled_rejection', 0)} controlled rejection; "
                f"{report.get('semantic_boundary_probes_incidental_failure', 0)} incidental failure; "
                f"{boundary_ne} not evaluable"
            )
            print(f"Semantic Boundary Variance: {report.get('semantic_boundary_variance_percentage')}")
    common_pack = result.get("common_test_pack") or {}
    if common_pack:
        print(
            "Common Test Pack: "
            f"{'READY' if common_pack.get('complete') else 'INCOMPLETE'} "
            f"({common_pack.get('suite_count', 0)} suites, {common_pack.get('test_count', 0)} tests)"
        )
    print(f"Batch JSON: {result.get('json_path')}")
    print(f"Batch CSV: {result.get('csv_path')}")
    dashboards = result.get('dashboards') or {}
    if dashboards:
        print(f"Dashboard generation: {dashboards.get('status')}")
        if dashboards.get('batch_dashboard'):
            print(f"Batch dashboard: {dashboards.get('batch_dashboard')}")
        if dashboards.get('comparative_dashboard'):
            print(
                f"Comparative dashboard ({dashboards.get('comparative_completed_agent_count', 0)} completed agent(s)): "
                f"{dashboards.get('comparative_dashboard')}"
            )
        if dashboards.get('error'):
            print(f"Dashboard warning: {dashboards.get('error')}")


def _report_llm_dataset_consistency(selection_dialog: InputSelectionDialog, result: dict) -> None:
    """Report study-level LLM algorithm-count/ID consistency after a batch.

    The first LLM dataset fixes the study denominator N. Later datasets are
    compared against that persisted study design. This is an operator warning
    only; already-written batch/scoring artefacts are never modified.
    """
    report = result.get("report") or {}
    if str(report.get("batch_type") or "").upper() != "LLM_RESULTS":
        return
    json_path = result.get("json_path")
    if not json_path:
        return
    try:
        results_root = Path(json_path).resolve().parent.parent
        from dashboard_generation import infer_study_root, update_study_algorithm_count_consistency

        study_root = infer_study_root(results_root, "LLM_RESULTS")
        if study_root is None:
            return
        consistency = update_study_algorithm_count_consistency(study_root)
    except Exception as error:
        print(f"WARNING: Could not evaluate LLM dataset count consistency: {error}", flush=True)
        return

    expected = int(consistency.get("expected_algorithm_count") or 0)
    dataset = str(report.get("dataset") or results_root.parent.name)
    checks = consistency.get("datasets") or []
    current = next((x for x in checks if str(x.get("results_directory") or "") == str(results_root)), None)
    if current is None:
        current = next((x for x in checks if str(x.get("dataset") or "") == dataset), None)
    if current is None:
        return

    actual = int(current.get("algorithm_count") or 0)
    if expected <= 0:
        message = (
            f"LLM dataset '{dataset}' contains no represented algorithms, so study algorithm count N could not be established.\n\n"
            "Please check the LLM input folder before adding further datasets."
        )
        print("WARNING: " + message.replace("\n", " | "), flush=True)
        show_info = getattr(selection_dialog, "show_info", None)
        if callable(show_info):
            show_info("WARNING — study algorithm count N not established", message)
        return
    if consistency.get("dataset_count") == 1 and current.get("status") == "MATCH":
        print(
            f"Study algorithm count N established: N={expected} from first LLM dataset '{dataset}'.",
            flush=True,
        )
        return
    if current.get("status") == "MATCH":
        print(f"LLM dataset count check: {dataset} matches study N={expected} ({actual}/{expected}).", flush=True)
        return

    missing = current.get("missing_algorithm_ids") or []
    extra = current.get("extra_algorithm_ids") or []
    lines = [
        "LLM DATASET COUNT MISMATCH",
        "",
        f"Study algorithm count N: {expected}",
        f"Reference dataset: {consistency.get('reference_dataset') or 'first LLM dataset'}",
        f"Dataset checked: {dataset}",
        f"Algorithms found: {actual}",
    ]
    if missing:
        lines.append("Missing algorithm IDs: " + ", ".join(str(x) for x in missing))
    if extra:
        lines.append("Extra algorithm IDs: " + ", ".join(str(x) for x in extra))
    lines.extend([
        "",
        "Please check this LLM input dataset before interpreting study-wide comparative or final-scoring metrics.",
        "The batch artefacts have been retained; N has NOT been changed.",
    ])
    message = "\n".join(lines)
    print("WARNING: " + message.replace("\n", " | "), flush=True)
    show_info = getattr(selection_dialog, "show_info", None)
    if callable(show_info):
        show_info("WARNING — LLM dataset count mismatch", message)


def _print_llm_run_header(
    selected_file: Path,
    selected_profile: PseudocodeProfile,
    selected_baseline_root: Path,
) -> None:
    pack_status = validate_common_test_pack(DEFAULT_COMMON_TESTS_ROOT)
    print(f"NL-FDEP pipeline version: {PIPELINE_VERSION}")
    print(f"Selected input type: {InputRoute.LLM_RESULTS_FOLDER.value}")
    print(f"Selected file: {selected_file.resolve()}")
    print(f"Selected pseudocode profile: {selected_profile.value}")
    print(f"Selected baseline root: {selected_baseline_root.resolve()}")
    print("Baseline role: PROCEDURAL_READINESS_GATE_ONLY (not supplied to experimental scoring)")
    baseline_state = _current_baseline_state(selected_baseline_root)
    baseline_b = _baseline_required_count(baseline_state)
    print(f"Baseline algorithm count B: {baseline_b} (expected Baseline Algorithms 1–{baseline_b})")
    if _baseline_study_ready(baseline_state):
        print(
            f"Baseline readiness: FULL_{baseline_b}_OF_{baseline_b}_PIPELINE_SUCCESS "
            f"({baseline_state['evaluated']}/{baseline_b} behaviourally evaluable; "
            "all evaluable calibrations at 100%)"
        )
    else:
        print("Baseline readiness: NOT_STUDY_READY")
    print(
        f"Packaged Common Tests v{TEST_DESIGN_VERSION}: "
        f"{'READY' if pack_status.complete else 'INCOMPLETE'} "
        f"({pack_status.suite_count} suites, {pack_status.test_count} tests)"
    )


def run_llm_study_session(
    selection_dialog: InputSelectionDialog,
    selected_profile: PseudocodeProfile,
    selected_baseline_root: Path | None = None,
    session_llm_results: list[Path] | None = None,
) -> None:
    """Run one or more LLM batches behind one explicit per-process baseline gate.

    A baseline calibrated earlier through the Baseline menu route can be supplied
    directly and remains active in memory for this runner process.
    """
    if selected_baseline_root is None:
        selected_baseline_root = establish_session_baseline(
            selection_dialog,
            selected_profile,
        )
    else:
        selected_baseline_root = Path(selected_baseline_root)
    if selected_baseline_root is None:
        print("Selected operation cancelled because no study-ready baseline benchmark was established.")
        return

    current_llm_results: Path | None = None
    session_llm_results = session_llm_results if session_llm_results is not None else []
    while True:
        if current_llm_results is None:
            current_llm_results = select_llm_results_directory(
                selection_dialog,
                selected_baseline_root,
            )

            # Re-check the in-memory session gate before every batch.  This does
            # not run the baseline or pass it into experimental scoring.
            current_state = _current_baseline_state(selected_baseline_root)
            if not _baseline_session_ready(selected_baseline_root, current_state):
                problems = _baseline_calibration_problem_details(selected_baseline_root)
                baseline_b = _baseline_required_count(current_state)
                selection_dialog.show_error(
                    "Baseline session is no longer study-ready",
                    "The active session baseline no longer satisfies the study-readiness gate.\n\n"
                    f"Required: {baseline_b}/{baseline_b} pipeline-successful baseline algorithms (Baseline Algorithms 1–{baseline_b}) and every "
                    "behaviourally evaluable calibration at 100%.\n"
                    f"Current: pipeline failures={current_state.get('pipeline_failure', 0)}; "
                    f"{current_state['evaluated']}/{baseline_b} evaluated; "
                    f"{current_state.get('full_score', 0)}/{current_state['evaluated']} evaluable "
                    "calibrations at 100%.\n\n"
                    f"Calibration problem details:\n{_format_baseline_calibration_problems(problems)}\n\n"
                    "The LLM batch has not started. Restart the runner and establish the baseline "
                    "gate again.",
                )
                return

            _print_llm_run_header(
                current_llm_results,
                selected_profile,
                selected_baseline_root,
            )
            result = run_selected_pipeline(
                route=InputRoute.LLM_RESULTS_FOLDER,
                input_path=current_llm_results,
                pseudocode_profile=selected_profile,
                baseline_root=selected_baseline_root,
            )
            _print_study_batch_result(InputRoute.LLM_RESULTS_FOLDER, result)
            _report_llm_dataset_consistency(selection_dialog, result)
            resolved_current = current_llm_results.resolve()
            if all(existing.resolve() != resolved_current for existing in session_llm_results):
                session_llm_results.append(current_llm_results)
            remembered_parent = remember_review_study(current_llm_results)
            if remembered_parent is not None:
                print(
                    f"Human Review previous-study context updated: {remembered_parent}",
                    flush=True,
                )

        action = selection_dialog.select_post_llm_action()
        if action == PostLLMAction.ANOTHER_LLM_RESULTS_FOLDER:
            current_llm_results = None
            continue
        if action == PostLLMAction.HUMAN_EVALUATION:
            run_human_review_folder(session_llm_results)
            print(
                "Human review session closed for "
                f"{len(session_llm_results)} LLM dataset(s) processed in this runner session."
            )
            # Keep the current batch active so the user can continue reviewing,
            # choose another LLM dataset, or quit after closing the dashboard.
            continue
        if action == PostLLMAction.QUIT:
            print("LLM study session closed.")
            return
        raise ValueError(f"Unsupported post-LLM action: {action}")


def _run_main_menu(selection_dialog: InputSelectionDialog) -> None:
    """Run the interactive route loop for one live runner process."""
    active_baseline_root: Path | None = None
    session_llm_results: list[Path] = []
    dependencies_verified = False

    while True:
        selected_profile: PseudocodeProfile | None = None
        human_review_startup_action: HumanReviewStartupAction | None = None

        try:
            selected_route = selection_dialog.select_route()
        except InputSelectionCancelledError as error:
            print(str(error))
            return

        if selected_route in {InputRoute.BASELINE_BENCHMARK_FOLDER, InputRoute.LLM_RESULTS_FOLDER}:
            if not dependencies_verified:
                if not ensure_runner_dependencies(selection_dialog):
                    print(
                        "Dependency verification was not completed. Baseline/LLM processing did not start.",
                        flush=True,
                    )
                    continue
                dependencies_verified = True

        if selected_route == InputRoute.LLM_RESULTS_FOLDER:
            try:
                selected_profile = selection_dialog.select_pseudocode_profile()
            except InputSelectionCancelledError as error:
                print(str(error))
                continue
            run_llm_study_session(
                selection_dialog,
                selected_profile,
                selected_baseline_root=active_baseline_root,
                session_llm_results=session_llm_results,
            )
            return

        if selected_route == InputRoute.PSEUDOCODE:
            try:
                selected_profile = selection_dialog.select_pseudocode_profile()
            except InputSelectionCancelledError as error:
                print(str(error))
                continue
        elif selected_route == InputRoute.BASELINE_BENCHMARK_FOLDER:
            selected_profile = BASELINE_CALIBRATION_PROFILE
        elif selected_route == InputRoute.HUMAN_REVIEW_FOLDER:
            try:
                human_review_startup_action = selection_dialog.select_human_review_startup_action()
            except InputSelectionCancelledError as error:
                print(str(error))
                continue

            if human_review_startup_action == HumanReviewStartupAction.RESUME_DISCOVER_EXISTING_STUDY:
                detected_roots = previous_study_review_roots()
                if detected_roots:
                    print(f"NL-FDEP pipeline version: {PIPELINE_VERSION}")
                    print(f"Selected input type: {selected_route.value}")
                    print(f"Human Review startup mode: {human_review_startup_action.value}")
                    print(
                        f"Previous study detected: {len(detected_roots)} completed experimental LLM dataset(s).",
                        flush=True,
                    )
                    run_human_review_folder(detected_roots, discover_siblings=False, regenerate_dashboards=True)
                    print("Human review session closed.")
                    return

                selection_dialog.show_info(
                    "No previous Human Review study detected",
                    "NL-FDEP could not find a remembered completed experimental study.\n\n"
                    "Select one LLM results folder once to establish the study location; future "
                    "Detect previous study sessions will open directly without asking for a folder.",
                )

        try:
            selected_file = selection_dialog.select_file(route=selected_route)
        except InputSelectionCancelledError as error:
            print(str(error))
            continue

        pack_status = validate_common_test_pack(DEFAULT_COMMON_TESTS_ROOT)
        print(f"NL-FDEP pipeline version: {PIPELINE_VERSION}")
        print(f"Selected input type: {selected_route.value}")
        print(f"Selected file: {selected_file.resolve()}")
        if selected_route == InputRoute.HUMAN_REVIEW_FOLDER and human_review_startup_action is not None:
            print(f"Human Review startup mode: {human_review_startup_action.value}")
        if selected_profile is not None:
            print(f"Selected pseudocode profile: {selected_profile.value}")
        print(
            f"Packaged Common Tests v{TEST_DESIGN_VERSION}: "
            f"{'READY' if pack_status.complete else 'INCOMPLETE'} "
            f"({pack_status.suite_count} suites, {pack_status.test_count} tests)"
        )

        if selected_route == InputRoute.BASELINE_BENCHMARK_FOLDER:
            baseline_preflight = validate_baseline(
                selected_file,
                common_tests_root=DEFAULT_COMMON_TESTS_ROOT,
            )
            if (
                not baseline_preflight.get("baseline_root_structure_valid")
                or baseline_preflight.get("issue_count", 0)
                or baseline_preflight.get("baseline_design_status") != "MATCH"
            ):
                design_note = _baseline_design_problem_summary(baseline_preflight)
                detail_parts = [
                    part for part in (design_note, _baseline_problem_summary(baseline_preflight)) if part
                ]
                selection_dialog.show_error(
                    "Baseline benchmark numbering/count mismatch",
                    "The Baseline set must define its own count B and contain exactly "
                    "Baseline Algorithms 1–B in both the pseudocode and reference-Python folders.\n\n"
                    + ("\n\n".join(detail_parts) or "Required baseline structure was not found.")
                    + "\n\nPlease check the Baseline input folders before calibration.",
                )
                continue
            baseline_b = int(baseline_preflight.get("baseline_algorithm_count") or 0)
            print(f"Baseline algorithm count B established from submitted Baseline set: B={baseline_b}")
            print(
                f"Baseline testing and calibration in progress — evaluating Baseline Algorithms 1–{baseline_b} "
                f"against Common Tests v{TEST_DESIGN_VERSION}…",
                flush=True,
            )
            result = run_selected_pipeline(
                route=selected_route,
                input_path=selected_file,
                pseudocode_profile=selected_profile,
            )
            _print_study_batch_result(selected_route, result)
            baseline_state = _current_baseline_state(selected_file)
            if _baseline_study_ready(baseline_state):
                active_baseline_root = Path(selected_file)
                _save_baseline_preference(active_baseline_root)
                print(
                    "Baseline calibration is study-ready and remains active for this runner session.",
                    flush=True,
                )
                print("Returning to the main options menu...", flush=True)
            else:
                active_baseline_root = None
                problems = _baseline_calibration_problem_details(
                    selected_file,
                    report=result.get("report", {}),
                )
                baseline_b = _baseline_required_count(baseline_state)
                selection_dialog.show_error(
                    "Baseline calibration is not study-ready",
                    "Baseline processing completed, but it cannot be activated for LLM processing.\n\n"
                    f"Required: {baseline_b}/{baseline_b} pipeline-successful baseline algorithms "
                    f"(Baseline Algorithms 1–{baseline_b}) and every behaviourally evaluable calibration at 100%.\n\n"
                    f"Calibration problem details:\n{_format_baseline_calibration_problems(problems)}",
                )
            continue

        if selected_route == InputRoute.HUMAN_REVIEW_FOLDER:
            review_result = run_human_review_folder(
                selected_file,
                discover_siblings=(
                    human_review_startup_action
                    == HumanReviewStartupAction.RESUME_DISCOVER_EXISTING_STUDY
                ),
                regenerate_dashboards=(
                    human_review_startup_action
                    == HumanReviewStartupAction.RESUME_DISCOVER_EXISTING_STUDY
                ),
            )
            if review_result.get("review_roots"):
                # Establish/update the harmless Human Review discovery pointer. This
                # does not persist baseline activation or any scoring state.
                remember_review_study(Path(review_result["review_roots"][0]))
            print("Human review session closed.")
            return

        result = run_selected_pipeline(
            route=selected_route,
            input_path=selected_file,
            pseudocode_profile=selected_profile,
        )
        print_pipeline_report(result=result)
        return


def main() -> None:
    """Run one NL-FDEP process with session-scoped baseline state.

    Orderly completion clears the external crash-recovery hint. Unexpected exceptions
    deliberately leave it untouched so the next launch can offer explicit recovery
    and full revalidation.
    """
    selection_dialog = InputSelectionDialog()
    try:
        _run_main_menu(selection_dialog)
    except Exception:
        raise
    else:
        _clear_baseline_preference()


if __name__ == "__main__":
    main()
