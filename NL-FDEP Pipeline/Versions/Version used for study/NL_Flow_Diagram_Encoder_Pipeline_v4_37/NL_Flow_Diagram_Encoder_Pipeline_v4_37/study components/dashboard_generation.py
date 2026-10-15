"""Automatic self-contained HTML dashboards for NL-FDEP study batches.

The dashboards are a presentation layer only. They read already-written study
artefacts and never participate in scoring, expected-value generation, baseline
calibration, or rubric adjudication.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import html
import json
import shutil

DASHBOARD_SCHEMA_VERSION = "1.0"
COLOUR_STOPS = [
    (0, "#2f6db3"),
    (25, "#6ec5ff"),
    (50, "#ffc145"),
    (75, "#9be564"),
    (100, "#2ca25f"),
]


def _read_json(path: Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _read_text(path: Path) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return None


def _results_child(parent: Path) -> Path | None:
    """Return a child named results, case-insensitively."""
    if not parent.is_dir():
        return None
    for child in parent.iterdir():
        if child.is_dir() and child.name.casefold() == "results":
            return child
    return None


def _algorithm_folder(parent: Path, algorithm_id: int) -> Path | None:
    wanted = f"algorithm - {algorithm_id}"
    if not parent.is_dir():
        return None
    for child in parent.iterdir():
        if child.is_dir() and child.name.casefold() == wanted:
            return child
    return None


def _source_pseudocode(folder: Path | None, algorithm_id: int) -> str | None:
    if folder is None:
        return None
    exact = folder / f"Algorithm {algorithm_id} Pseudocode.txt"
    if exact.is_file():
        return _read_text(exact)
    target = f"algorithm {algorithm_id} pseudocode.txt"
    for child in folder.iterdir():
        if child.is_file() and " ".join(child.name.split()).casefold() == target:
            return _read_text(child)
    return None


def _generated_python(folder: Path | None) -> tuple[str | None, str | None]:
    if folder is None:
        return None, None
    path = folder / "pipeline_artifacts" / "generated_program.py"
    if not path.is_file():
        return None, None
    return _read_text(path), str(path.resolve())


def _safe_json_for_script(value: Any) -> str:
    # Prevent source text containing </script> from terminating the data script.
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def _number(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _report_algorithm_ids(report: dict[str, Any], rows: dict[int, dict[str, Any]] | None = None) -> list[int]:
    """Return the algorithm IDs represented by an already-written batch report.

    ``algorithm_count`` is the authoritative dataset-size field written by the
    batch processor. Explicit IDs are retained when the report contains the full
    set; older/minimal reports fall back to the conventional contiguous 1..N set.
    """
    try:
        declared_count = max(0, int(report.get("algorithm_count") or 0))
    except (TypeError, ValueError):
        declared_count = 0
    ids: set[int] = set()
    for item in report.get("algorithms") or []:
        if not isinstance(item, dict):
            continue
        raw = item.get("algorithm_id", item.get("algorithm", item.get("Algorithm")))
        try:
            aid = int(raw)
        except (TypeError, ValueError):
            continue
        if aid > 0:
            ids.add(aid)
    if rows:
        ids.update(int(aid) for aid in rows if int(aid) > 0)
    if declared_count > 0 and len(ids) != declared_count:
        return list(range(1, declared_count + 1))
    if ids:
        return sorted(ids)
    return list(range(1, declared_count + 1)) if declared_count > 0 else []


def _report_algorithm_count(report: dict[str, Any], rows: dict[int, dict[str, Any]] | None = None) -> int:
    try:
        declared = max(0, int(report.get("algorithm_count") or 0))
    except (TypeError, ValueError):
        declared = 0
    return declared or len(_report_algorithm_ids(report, rows))


def _mean(values: list[Any]) -> float | None:
    nums = [_number(v) for v in values]
    nums = [v for v in nums if v is not None]
    return round(sum(nums) / len(nums), 2) if nums else None


def _combined_behavioural(report: dict[str, Any]) -> float | None:
    a = _number(report.get("mean_experimental_behavioural_percentage"))
    b = _number(report.get("semantic_test_accuracy_percentage"))
    if a is None or b is None:
        return None
    return round((a + b) / 2.0, 2)


def _row_map(analysis_directory: Path) -> dict[int, dict[str, Any]]:
    rows = _read_json(analysis_directory / "algorithm_scores.json")
    out: dict[int, dict[str, Any]] = {}
    if not isinstance(rows, list):
        return out
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            aid = int(row.get("Algorithm"))
        except (TypeError, ValueError):
            continue
        out[aid] = row
    return out


def _batch_records(report: dict[str, Any]) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    for record in report.get("algorithms", []) or []:
        if not isinstance(record, dict):
            continue
        try:
            aid = int(record.get("algorithm_id"))
        except (TypeError, ValueError):
            continue
        out[aid] = record
    return out


def _human_review_record(folder: Path | None, algorithm_id: int) -> dict[str, Any]:
    """Read existing review/adjudication artefacts without changing study state."""
    if folder is None:
        return {
            "algorithm": algorithm_id,
            "reviewPresent": False,
            "questionnaireGenerated": False,
            "status": "PENDING",
            "criteriaCompleted": 0,
            "criteriaTotal": 16,
            "humanRubric": None,
            "automatedRubric": None,
            "combinedRubric": None,
            "combinedAvailable": False,
            "agreementPercentage": None,
            "reviewer": {},
            "sourceSufficiency": {},
            "behaviouralEvidenceAdequacy": {},
            "taskSemanticEvaluation": {},
            "overallReview": {},
            "criteria": [],
            "stageHumanPercentages": {},
            "semanticIssueCount": 0,
            "agreementCounts": {},
        }

    scoring = folder / "pipeline_artifacts" / "scoring"
    final_score = _read_json(scoring / "final_score.json")
    human_review = _read_json(scoring / "human_review.json")
    if not isinstance(final_score, dict):
        final_score = {}
    if not isinstance(human_review, dict):
        human_review = {}

    reviewer_raw = human_review.get("reviewer") or {}
    review_meta = final_score.get("review") or {}
    reviewer = {
        "reviewerId": reviewer_raw.get("reviewer_id") or review_meta.get("reviewer_id"),
        "reviewerName": reviewer_raw.get("reviewer_name"),
        "reviewedAtUtc": reviewer_raw.get("reviewed_at_utc") or review_meta.get("reviewed_at_utc"),
        "confidence": reviewer_raw.get("overall_reviewer_confidence") or review_meta.get("overall_reviewer_confidence"),
    }

    rubric = final_score.get("rubric_scores") or {}
    automated = rubric.get("automated") or {}
    human = rubric.get("human") or {}
    combined = rubric.get("combined") or {}
    criteria_total = human.get("criteria_total")
    criteria_completed = human.get("criteria_completed")

    criteria: list[dict[str, Any]] = []
    agreement_counts: dict[str, int] = {}
    semantic_issue_count = 0
    for stage_key, stage in (final_score.get("stages") or {}).items():
        if not isinstance(stage, dict):
            continue
        for criterion in stage.get("criteria", []) or []:
            if not isinstance(criterion, dict):
                continue
            auto = criterion.get("automated_assessment") or {}
            h = criterion.get("human_assessment") or {}
            agreement = h.get("agreement_with_automated_score")
            if agreement:
                agreement_counts[str(agreement)] = agreement_counts.get(str(agreement), 0) + 1
            if h.get("semantic_issue") is True:
                semantic_issue_count += 1
            criteria.append({
                "stageKey": stage_key,
                "stageName": stage.get("stage_name"),
                "criterionId": criterion.get("criterion_id"),
                "question": criterion.get("question"),
                "criticalSemanticCriterion": bool(criterion.get("critical_semantic_criterion")),
                "automatedScore": auto.get("score"),
                "automatedStatus": auto.get("status"),
                "automatedConfidence": auto.get("confidence"),
                "automatedJustification": auto.get("justification"),
                "humanCompleted": bool(h.get("completed")),
                "humanScore": h.get("score"),
                "humanScoreLabel": h.get("score_label"),
                "humanStatus": h.get("status"),
                "agreement": agreement,
                "semanticIssue": h.get("semantic_issue"),
                "reviewerJustification": h.get("reviewer_justification"),
            })

    if criteria_total is None:
        criteria_total = len(criteria) or 16
    if criteria_completed is None:
        criteria_completed = sum(1 for c in criteria if c.get("humanCompleted"))

    raw_status = review_meta.get("status")
    if human.get("complete") or (criteria_total and criteria_completed == criteria_total):
        status = "COMPLETED"
    elif criteria_completed:
        status = "PARTIAL"
    elif human_review:
        status = str(raw_status or "EMPTY")
    else:
        status = "PENDING"

    source = human_review.get("source_sufficiency") or {}
    source_final = final_score.get("source_sufficiency") or {}
    source_human = source_final.get("human_assessment") or {}
    g2 = human_review.get("behavioural_evidence_adequacy") or {}
    g2_final = final_score.get("behavioural_evidence_adequacy") or {}
    g2_human = g2_final.get("human_assessment") or {}
    task = human_review.get("task_semantic_evaluation") or {}
    overall = human_review.get("overall_review") or review_meta.get("overall_review") or {}

    stage_human = {}
    for stage_key, stage in (final_score.get("stages") or {}).items():
        if isinstance(stage, dict):
            stage_human[stage_key] = (stage.get("human_stage_summary") or {}).get("percentage")

    return {
        "algorithm": algorithm_id,
        "reviewPresent": bool(human_review),
        "questionnaireGenerated": (scoring / "human_review_questionnaire.html").is_file(),
        "status": status,
        "scoreStatus": final_score.get("score_status"),
        "criteriaCompleted": criteria_completed or 0,
        "criteriaTotal": criteria_total or 16,
        "humanRubric": human.get("percentage"),
        "automatedRubric": automated.get("percentage"),
        "combinedRubric": combined.get("percentage"),
        "combinedAvailable": bool(combined.get("available")),
        "agreementPercentage": (final_score.get("derived_metrics") or {}).get("automated_human_agreement_percentage"),
        "reviewer": reviewer,
        "sourceSufficiency": {
            "automatedResult": source_final.get("result") or source.get("automated_result"),
            "humanResult": source_human.get("result") or source.get("human_result"),
            "agreement": source_human.get("agreement_with_automated_result") or source.get("agreement_with_automated_result"),
            "reviewerJustification": source_human.get("reviewer_justification") or source.get("reviewer_justification"),
        },
        "behaviouralEvidenceAdequacy": {
            "automatedResult": g2_final.get("result") or g2.get("automated_result"),
            "humanResult": g2_human.get("result") or g2.get("human_result"),
            "agreement": g2_human.get("agreement_with_automated_result") or g2.get("agreement_with_automated_result"),
            "reviewerJustification": g2_human.get("reviewer_justification") or g2.get("reviewer_justification"),
        },
        "taskSemanticEvaluation": task.get("human_assessment") or {},
        "overallReview": overall,
        "criteria": criteria,
        "stageHumanPercentages": stage_human,
        "semanticIssueCount": semantic_issue_count,
        "agreementCounts": agreement_counts,
    }


def _batch_dashboard_data(batch_root: Path, analysis_directory: Path) -> dict[str, Any]:
    report = _read_json(analysis_directory / "batch_report.json") or {}
    rows = _row_map(analysis_directory)
    records = _batch_records(report)
    is_baseline = str(report.get("batch_type") or "").upper() == "BASELINE"
    dataset = str(report.get("dataset") or batch_root.name)
    algorithm_ids = _report_algorithm_ids(report, rows)
    algorithms = []
    for aid in algorithm_ids:
        row = rows.get(aid, {})
        record = records.get(aid, {})
        folder = _algorithm_folder(batch_root, aid)
        pseudo = _source_pseudocode(folder, aid)
        generated, generated_path = _generated_python(folder)
        human_review = _human_review_record(folder, aid)
        score = (
            row.get("BaselineCalibrationPercent")
            if is_baseline
            else row.get("ExperimentalBehaviouralPercent")
        )
        if score is None:
            score = record.get("baseline_calibration_percentage" if is_baseline else "experimental_behavioural_percentage")
        algorithms.append({
            "algorithm": aid,
            "score": _number(score),
            "comparison": row.get("ComparisonToBaseline") or record.get("comparison_to_baseline") or ("CALIBRATION" if is_baseline else "NOT_EVALUABLE"),
            "pipelineStatus": row.get("PipelineStatus") or record.get("status") or "NOT_RUN",
            "pipelineSuccess": row.get("PipelineSuccess") if row.get("PipelineSuccess") is not None else record.get("pipeline_success"),
            "batchAction": row.get("BatchAction") or record.get("action"),
            "batchError": row.get("BatchError") or record.get("error"),
            "canonicalisation": _number(row.get("CanonicalisationPercent")),
            "ast": _number(row.get("ASTPercent")),
            "flow": _number(row.get("FlowPercent")),
            "python": _number(row.get("PythonPercent")),
            "testAccuracy": _number(row.get("TestAccuracyPercent")),
            "automatedRubric": _number(row.get("AutomatedRubricPercent")),
            "humanRubric": _number(row.get("HumanRubricPercent")),
            "combinedRubric": _number(row.get("CombinedRubricPercent")),
            "combinedRubricAvailable": bool(row.get("CombinedRubricAvailable")),
            "boundaryVariance": _number(row.get("SemanticBoundaryVariancePercent")),
            "boundaryEvaluable": row.get("SemanticBoundaryProbesEvaluable") if row else record.get("semantic_boundary_probes_evaluable"),
            "boundaryAccepted": row.get("SemanticBoundaryAccepted") if row else record.get("semantic_boundary_probes_accepted"),
            "boundaryControlled": row.get("SemanticBoundaryControlledRejection") if row else record.get("semantic_boundary_probes_controlled_rejection"),
            "boundaryIncidental": row.get("SemanticBoundaryIncidentalFailure") if row else record.get("semantic_boundary_probes_incidental_failure"),
            "behaviouralEvidenceAdequacy": row.get("BehaviouralEvidenceAdequacy"),
            "g2Summary": row.get("G2Summary"),
            "g2Strengths": row.get("G2Strengths"),
            "g2Limitations": row.get("G2Limitations"),
            "failureTaxonomy": row.get("FailureTaxonomy"),
            "firstSemanticLossStage": row.get("FirstSemanticLossStage"),
            "firstSemanticLossCriterion": row.get("FirstSemanticLossCriterion"),
            "cyclomaticComplexity": row.get("CyclomaticComplexity"),
            "decisionCount": row.get("DecisionCount"),
            "loopCount": row.get("LoopCount"),
            "maximumLoopNesting": row.get("MaximumLoopNesting"),
            "pseudocode": pseudo,
            "generatedPython": generated,
            "generatedPythonPath": generated_path,
            "humanReview": human_review,
        })

    review_records = [a.get("humanReview") or {} for a in algorithms]
    review_present = sum(1 for r in review_records if r.get("reviewPresent"))
    review_completed = sum(1 for r in review_records if r.get("status") == "COMPLETED")
    review_partial = sum(1 for r in review_records if r.get("status") in {"PARTIAL", "EMPTY"})
    reviewer_ids = {str((r.get("reviewer") or {}).get("reviewerId")) for r in review_records if (r.get("reviewer") or {}).get("reviewerId")}
    return {
        "schemaVersion": DASHBOARD_SCHEMA_VERSION,
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "dataset": dataset,
        "batchType": report.get("batch_type"),
        "isBaseline": is_baseline,
        "report": {
            "algorithmCount": _report_algorithm_count(report, rows),
            "meanBehavioural": report.get("mean_experimental_behavioural_percentage"),
            "commonTestAccuracy": report.get("semantic_test_accuracy_percentage"),
            "combinedBehavioural": _combined_behavioural(report),
            "boundaryVariance": report.get("semantic_boundary_variance_percentage"),
            "meanBoundaryVariance": report.get("mean_algorithm_semantic_boundary_variance_percentage"),
            "meanBaselineCalibration": report.get("mean_baseline_calibration_percentage"),
            "semanticTestsEvaluable": report.get("semantic_tests_evaluable"),
            "semanticTestsPassed": report.get("semantic_tests_passed"),
            "semanticTestsNotEvaluable": report.get("semantic_tests_not_evaluable"),
            "pipelineStatusCounts": report.get("pipeline_status_counts") or report.get("status_counts") or {},
            "comparisonCounts": report.get("comparison_to_baseline_counts") or {},
            "boundaryEvaluable": report.get("semantic_boundary_probes_evaluable"),
            "boundaryAccepted": report.get("semantic_boundary_probes_accepted"),
            "boundaryControlled": report.get("semantic_boundary_probes_controlled_rejection"),
            "boundaryIncidental": report.get("semantic_boundary_probes_incidental_failure"),
            "boundaryNotEvaluable": report.get("semantic_boundary_probes_not_evaluable"),
            "meanAutomatedRubric": _mean([r.get("AutomatedRubricPercent") for r in rows.values()]),
            "meanHumanRubric": _mean([r.get("humanRubric") for r in review_records]),
            "meanCombinedRubric": _mean([r.get("combinedRubric") for r in review_records if r.get("combinedAvailable")]),
            "humanReviewPresent": review_present,
            "humanReviewCompleted": review_completed,
            "humanReviewPartial": review_partial,
            "humanReviewPending": max(0, len(algorithm_ids) - review_completed - review_partial),
            "humanReviewerCount": len(reviewer_ids),
            "meanHumanAgreement": _mean([r.get("agreementPercentage") for r in review_records]),
            "humanCriteriaCompleted": sum(int(r.get("criteriaCompleted") or 0) for r in review_records),
            "humanCriteriaTotal": sum(int(r.get("criteriaTotal") or 0) for r in review_records),
            "humanSemanticIssues": sum(int(r.get("semanticIssueCount") or 0) for r in review_records),
        },
        "algorithms": algorithms,
    }


_COMMON_CSS = r"""
:root{--bg:#f7f9fc;--panel:#fff;--text:#172033;--muted:#667085;--border:#d9e0ea;--shadow:0 12px 30px rgba(16,24,40,.08);--accent:#315efb}
*{box-sizing:border-box}body{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--bg);color:var(--text)}
.page{max-width:1700px;margin:0 auto;padding:24px}.panel{background:var(--panel);border:1px solid var(--border);border-radius:16px;box-shadow:var(--shadow)}
h1{margin:0 0 6px;font-size:clamp(1.65rem,2.8vw,2.45rem);letter-spacing:-.03em}.sub{margin:0 0 18px;color:var(--muted);line-height:1.5}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:12px;margin:0 0 18px}.card{padding:13px 15px}.card .k{font-size:.75rem;color:var(--muted)}.card .v{font-weight:800;font-size:1.28rem;margin-top:3px}
.toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:12px 14px;margin-bottom:16px}button,select{font:inherit;border:1px solid var(--border);background:#fff;padding:7px 9px;border-radius:9px;color:var(--text)}button{cursor:pointer;font-weight:700}
.legend{display:flex;flex-wrap:wrap;gap:10px;align-items:center;font-size:.78rem;color:#52606f;margin:10px 0}.sw{width:15px;height:15px;border:1px solid rgba(0,0,0,.15);border-radius:3px;display:inline-block;vertical-align:middle;margin-right:4px}
.heat-wrap{padding:14px}.alg-head,.heat-row{display:grid;grid-template-columns:repeat(50,minmax(0,1fr));gap:2px}.alg-head div{text-align:center;font-size:8px;color:var(--muted);overflow:hidden}.cell{aspect-ratio:1/1;min-height:17px;border:1px solid rgba(0,0,0,.10);border-radius:3px;cursor:pointer;position:relative;display:flex;align-items:center;justify-content:center;font-size:8px;font-weight:800;overflow:hidden}.cell:hover,.cell.sel{outline:2px solid #172033;z-index:2}.cell.dim{opacity:.18}.sep{box-shadow:2px 0 0 #7f8b9e}
.grid2{display:grid;grid-template-columns:minmax(0,1fr) 390px;gap:16px;align-items:start}.detail{padding:16px;position:sticky;top:12px;max-height:calc(100vh - 24px);overflow:auto}.detail h2{margin:0 0 4px}.muted{color:var(--muted)}
.sec{border-top:1px solid var(--border);margin-top:12px;padding-top:12px}.sec h3{margin:0 0 8px;font-size:.9rem}.kvgrid{display:grid;grid-template-columns:1fr 1fr;gap:8px 12px}.kv .k{font-size:.7rem;color:var(--muted)}.kv .v{font-size:.86rem;font-weight:700;overflow-wrap:anywhere}
.codebox{border:1px solid var(--border);border-radius:10px;overflow:hidden;margin-top:8px}.codehead{display:flex;justify-content:space-between;align-items:center;padding:7px 9px;background:#f4f6f9;font-size:.76rem;font-weight:700}.codebox pre{margin:0;padding:10px;max-height:280px;overflow:auto;background:#101828;color:#f2f4f7;font-size:.76rem;line-height:1.45;white-space:pre}
.tablewrap{overflow:auto}.rank{width:100%;border-collapse:collapse;font-size:.84rem}.rank th,.rank td{padding:8px 9px;border-bottom:1px solid var(--border);text-align:left}.rank th{color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.04em}.rank td.num{text-align:right;font-variant-numeric:tabular-nums}
.bar{height:9px;background:#e9eef5;border-radius:999px;overflow:hidden;min-width:90px}.bar>i{display:block;height:100%;background:#667085;border-radius:999px}
.badge{display:inline-block;border:1px solid var(--border);border-radius:999px;padding:3px 7px;font-size:.7rem;background:#fff}.warn{background:#fff7e6}.ok{background:#ecfdf3}.fail{background:#fff1f0}
@media(max-width:1050px){.grid2{grid-template-columns:1fr}.detail{position:static;max-height:none}.page{padding:14px}.cell{min-height:13px;font-size:0}.alg-head div{font-size:0}.alg-head div:nth-child(5n){font-size:7px}.kvgrid{grid-template-columns:1fr}}
"""


def _batch_html(data: dict[str, Any]) -> str:
    data_json = _safe_json_for_script(data)
    title = html.escape(f"NL-FDEP — {data['dataset']} Batch Dashboard")
    algorithm_count = int((data.get("report") or {}).get("algorithmCount") or len(data.get("algorithms") or []))
    return f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{_COMMON_CSS}</style></head>
<body><div class="page"><h1>{title}</h1><p class="sub">Automatically generated from the completed NL-FDEP batch artefacts. Dashboard presentation does not participate in scoring.</p>
<div id="cards" class="cards"></div><div class="toolbar panel"><strong>Algorithm view</strong><select id="filter"><option value="all">All algorithms</option><option value="at">At reference</option><option value="below">Below reference</option><option value="ne">Not evaluable</option><option value="fail">Pipeline failures</option><option value="boundary">Boundary probes evaluable</option></select><select id="labels"><option value="score">Cell text: score</option><option value="id">Cell text: algorithm</option><option value="none">Cell text: none</option></select><button id="clear">Clear selection</button></div>
<div class="grid2"><div><div class="panel heat-wrap"><div style="display:flex;justify-content:space-between;gap:12px;align-items:end;flex-wrap:wrap"><div><strong id="heatTitle">{algorithm_count}-algorithm behavioural heat map</strong><div class="muted" style="font-size:.8rem;margin-top:3px">All {algorithm_count} algorithms remain visible. White = not evaluable / no behavioural score.</div></div></div><div class="alg-head" id="head"></div><div class="heat-row" id="heat"></div><div class="legend"><strong>Behavioural score:</strong><span><i class="sw" style="background:#2f6db3"></i>0</span><span><i class="sw" style="background:#6ec5ff"></i>25</span><span><i class="sw" style="background:#ffc145"></i>50</span><span><i class="sw" style="background:#9be564"></i>75</span><span><i class="sw" style="background:#2ca25f"></i>100</span><span><i class="sw" style="background:#fff"></i>Not evaluable</span></div></div>
<div class="panel" style="margin-top:16px;padding:14px"><h2 style="margin-top:0;font-size:1.05rem">Algorithm table</h2><div class="tablewrap"><table class="rank"><thead><tr><th>Alg.</th><th>Behavioural</th><th>Reference</th><th>Pipeline</th><th>Review</th><th>Human rubric</th><th>Agreement</th><th>SBV</th><th>Automated rubric</th><th>Combined rubric</th></tr></thead><tbody id="tbody"></tbody></table></div></div></div>
<div class="panel detail" id="detail"><h2>Algorithm inspection</h2><p class="muted">Select a heat-map cell or table row.</p></div></div></div>
<script>const DATA={data_json};
const A=DATA.algorithms;let selected=null;const $=s=>document.querySelector(s);const esc=v=>String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;');
const pct=v=>v==null||Number.isNaN(+v)?'—':(+v).toFixed(2)+'%';const pretty=v=>v==null||v===''?'—':String(v).replaceAll('_',' ');
function colour(v){{if(v==null)return '#fff';const stops=[[0,[47,109,179]],[25,[110,197,255]],[50,[255,193,69]],[75,[155,229,100]],[100,[44,162,95]]];v=Math.max(0,Math.min(100,+v));for(let i=1;i<stops.length;i++){{if(v<=stops[i][0]){{const [x0,c0]=stops[i-1],[x1,c1]=stops[i],t=(v-x0)/(x1-x0);const c=c0.map((q,j)=>Math.round(q+(c1[j]-q)*t));return `rgb(${{c[0]}},${{c[1]}},${{c[2]}})`;}}}}return '#2ca25f';}}
function card(k,v){{return `<div class="panel card"><div class="k">${{esc(k)}}</div><div class="v">${{esc(v)}}</div></div>`;}}
function renderCards(){{const r=DATA.report,isB=DATA.isBaseline;const parts=[card('Dataset',DATA.dataset),card('Algorithms',r.algorithmCount??A.length)];if(isB)parts.push(card('Mean baseline calibration',pct(r.meanBaselineCalibration)));else{{parts.push(card('Mean semantic behavioural',pct(r.meanBehavioural)),card('Common Test accuracy',pct(r.commonTestAccuracy)),card('Combined Behavioural Measure',pct(r.combinedBehavioural)),card('Semantic Boundary Variance',pct(r.boundaryVariance)));}}if(r.meanHumanRubric!=null)parts.push(card('Mean Human Rubric',pct(r.meanHumanRubric)));if(r.meanCombinedRubric!=null)parts.push(card('Mean Combined Rubric',pct(r.meanCombinedRubric)));parts.push(card('Human reviews completed',`${{r.humanReviewCompleted??0}} / ${{r.algorithmCount??A.length}}`),card('Human reviews partial',r.humanReviewPartial??0),card('Reviewers',r.humanReviewerCount??0),card('Mean human/auto agreement',pct(r.meanHumanAgreement)));$('#cards').innerHTML=parts.join('');$('#heatTitle').textContent=isB?`${{r.algorithmCount??A.length}}-algorithm baseline calibration heat map`:`${{r.algorithmCount??A.length}}-algorithm behavioural heat map`;}}
function match(r,m){{if(m==='all')return true;if(m==='at')return r.comparison==='AT_REFERENCE';if(m==='below')return r.comparison==='BELOW_REFERENCE';if(m==='ne')return r.score==null;if(m==='fail')return r.pipelineStatus==='FAILURE';if(m==='boundary')return +(r.boundaryEvaluable||0)>0;return true;}}
function renderHeat(){{const mode=$('#filter').value,lm=$('#labels').value;$('#head').style.gridTemplateColumns=`repeat(${{A.length}},minmax(0,1fr))`;$('#heat').style.gridTemplateColumns=`repeat(${{A.length}},minmax(0,1fr))`;$('#head').innerHTML=A.map(r=>`<div>${{r.algorithm}}</div>`).join('');$('#heat').innerHTML=A.map(r=>{{const lab=lm==='score'?(r.score==null?'':Math.round(r.score)):lm==='id'?r.algorithm:'';const text=r.score!=null&&r.score<42?'#fff':'#172033';return `<div class="cell ${{r.algorithm%5===0?'sep ':''}}${{selected===r.algorithm?'sel ':''}}${{match(r,mode)?'':'dim'}}" data-id="${{r.algorithm}}" title="Algorithm ${{r.algorithm}} — ${{pct(r.score)}}" style="background:${{colour(r.score)}};color:${{text}}">${{lab}}</div>`;}}).join('');document.querySelectorAll('.cell').forEach(x=>x.onclick=()=>selectAlg(+x.dataset.id));}}
function renderTable(){{const mode=$('#filter').value;$('#tbody').innerHTML=A.map(r=>{{const h=r.humanReview||{{}};return `<tr data-id="${{r.algorithm}}" style="${{match(r,mode)?'':'opacity:.25'}};cursor:pointer"><td>${{r.algorithm}}</td><td class="num">${{pct(r.score)}}</td><td>${{pretty(r.comparison)}}</td><td>${{pretty(r.pipelineStatus)}}</td><td>${{pretty(h.status||'PENDING')}}</td><td class="num">${{pct(h.humanRubric)}}</td><td class="num">${{pct(h.agreementPercentage)}}</td><td class="num">${{pct(r.boundaryVariance)}}</td><td class="num">${{pct(r.automatedRubric)}}</td><td class="num">${{r.combinedRubricAvailable?pct(r.combinedRubric):'—'}}</td></tr>`;}}).join('');document.querySelectorAll('#tbody tr').forEach(x=>x.onclick=()=>selectAlg(+x.dataset.id));}}
function kv(k,v){{return `<div class="kv"><div class="k">${{esc(k)}}</div><div class="v">${{esc(v??'—')}}</div></div>`;}}
window.copyCode=async function(btn){{const code=btn.closest('.codebox').querySelector('code').innerText,old=btn.textContent;const done=t=>{{btn.textContent=t;setTimeout(()=>btn.textContent=old,1300)}};if(navigator.clipboard&&navigator.clipboard.writeText){{try{{await navigator.clipboard.writeText(code);done('Copied');return}}catch(e){{}}}}try{{const t=document.createElement('textarea');t.value=code;t.style.position='fixed';t.style.opacity='.01';document.body.appendChild(t);t.focus();t.select();const ok=document.execCommand&&document.execCommand('copy');t.remove();if(ok){{done('Copied');return}}}}catch(e){{}}const el=btn.closest('.codebox').querySelector('code'),s=window.getSelection(),range=document.createRange();range.selectNodeContents(el);s.removeAllRanges();s.addRange(range);done('Selected — Ctrl+C');}};
function codebox(title,code,path){{if(!code)return `<div class="muted">No ${{esc(title.toLowerCase())}} artefact is available.</div>`;return `<div class="codebox"><div class="codehead"><span>${{esc(title)}}${{path?` <span class="muted">· ${{esc(path)}}</span>`:''}}</span><button onclick="copyCode(this)">Copy</button></div><pre><code>${{esc(code)}}</code></pre></div>`;}}
function reviewCriteriaTable(h){{const rows=(h.criteria||[]).map(c=>`<tr><td><strong>${{esc(c.criterionId||'—')}}</strong><div class="muted" style="font-size:.7rem">${{esc(c.stageName||c.stageKey||'')}}</div></td><td>${{esc(c.question||'—')}}</td><td class="num">${{c.automatedScore??'—'}}</td><td class="num">${{c.humanCompleted?(c.humanScoreLabel??c.humanScore??'—'):'—'}}</td><td>${{pretty(c.agreement)}}</td><td>${{c.semanticIssue===true?'Yes':c.semanticIssue===false?'No':'—'}}</td><td>${{esc(c.reviewerJustification||'—')}}</td></tr>`).join('');return `<div class="tablewrap"><table class="rank"><thead><tr><th>Criterion</th><th>Question</th><th>Auto</th><th>Human</th><th>Agreement</th><th>Semantic issue</th><th>Reviewer justification</th></tr></thead><tbody>${{rows||'<tr><td colspan="7">No completed human criterion assessments.</td></tr>'}}</tbody></table></div>`;}}
function humanReviewSection(h){{h=h||{{}};const rv=h.reviewer||{{}},ss=h.sourceSufficiency||{{}},g2=h.behaviouralEvidenceAdequacy||{{}},ts=h.taskSemanticEvaluation||{{}},ov=h.overallReview||{{}};return `<div class="sec"><h3>Human review</h3><div class="kvgrid">${{kv('Review status',pretty(h.status||'PENDING'))}}${{kv('Criteria completed',`${{h.criteriaCompleted??0}} / ${{h.criteriaTotal??16}}`)}}${{kv('Reviewer ID',rv.reviewerId)}}${{kv('Reviewer name',rv.reviewerName)}}${{kv('Reviewed at UTC',rv.reviewedAtUtc)}}${{kv('Reviewer confidence',rv.confidence)}}${{kv('Human rubric',pct(h.humanRubric))}}${{kv('Automated/human agreement',pct(h.agreementPercentage))}}${{kv('Semantic issues marked',h.semanticIssueCount??0)}}${{kv('Combined rubric',h.combinedAvailable?pct(h.combinedRubric):'—')}}</div></div><div class="sec"><h3>Human gate and semantic assessments</h3><div class="kvgrid">${{kv('Source sufficiency — human',pretty(ss.humanResult))}}${{kv('Source sufficiency agreement',pretty(ss.agreement))}}${{kv('Behavioural evidence — human',pretty(g2.humanResult))}}${{kv('Behavioural evidence agreement',pretty(g2.agreement))}}${{kv('Required inputs represented',pretty(ts.required_inputs_represented))}}${{kv('Core algorithm logic',pretty(ts.core_algorithm_logic))}}${{kv('Required output semantics',pretty(ts.required_output_semantics_represented))}}${{kv('Edge/domain handling',pretty(ts.edge_and_domain_handling))}}${{kv('Overall semantic assessment',pretty(ts.overall_semantic_assessment))}}${{kv('Material semantic error not captured',pretty(ov.material_semantic_error_not_captured))}}${{kv('First semantic loss stage',pretty(ov.first_semantic_loss_stage))}}${{kv('Final Python behaviourally faithful',pretty(ov.final_python_behaviourally_faithful))}}</div><p class="muted" style="font-size:.78rem"><strong>Source sufficiency justification:</strong> ${{esc(ss.reviewerJustification||'—')}}</p><p class="muted" style="font-size:.78rem"><strong>Behavioural evidence justification:</strong> ${{esc(g2.reviewerJustification||'—')}}</p><p class="muted" style="font-size:.78rem"><strong>Semantic review justification:</strong> ${{esc(ts.reviewer_justification||'—')}}</p><p class="muted" style="font-size:.78rem"><strong>Additional observations:</strong> ${{esc(ov.additional_observations||'—')}}</p></div><div class="sec"><h3>Criterion-level human review</h3>${{reviewCriteriaTable(h)}}</div>`;}}
function selectAlg(id){{selected=id;const r=A.find(x=>x.algorithm===id);renderHeat();if(!r)return;$('#detail').innerHTML=`<h2>Algorithm ${{id}}</h2><p class="muted">${{esc(DATA.dataset)}} · ${{pretty(r.pipelineStatus)}}</p><div class="sec"><h3>Behavioural result</h3><div class="kvgrid">${{kv('Behavioural score',pct(r.score))}}${{kv('Reference comparison',pretty(r.comparison))}}${{kv('Semantic Boundary Variance',pct(r.boundaryVariance))}}${{kv('Boundary probes evaluable',r.boundaryEvaluable)}}${{kv('Out-of-domain accepted',r.boundaryAccepted)}}${{kv('Controlled rejection',r.boundaryControlled)}}${{kv('Incidental failure',r.boundaryIncidental)}}${{kv('Evidence adequacy',pretty(r.behaviouralEvidenceAdequacy))}}</div></div><div class="sec"><h3>Assessed pseudocode</h3>${{codebox('Pseudocode',r.pseudocode,null)}}</div><div class="sec"><h3>Generated Python</h3>${{codebox('Python produced by NL-FDEP',r.generatedPython,r.generatedPythonPath)}}</div><div class="sec"><h3>Transformation stages</h3><div class="kvgrid">${{kv('Canonicalisation',pct(r.canonicalisation))}}${{kv('AST',pct(r.ast))}}${{kv('Flow',pct(r.flow))}}${{kv('Python',pct(r.python))}}${{kv('Test accuracy',pct(r.testAccuracy))}}${{kv('Automated rubric',pct(r.automatedRubric))}}${{kv('Human rubric',pct(r.humanRubric))}}${{kv('Combined rubric',r.combinedRubricAvailable?pct(r.combinedRubric):'—')}}</div></div>${{humanReviewSection(r.humanReview)}}<div class="sec"><h3>Pipeline / semantic loss</h3><div class="kvgrid">${{kv('Failure taxonomy',pretty(r.failureTaxonomy))}}${{kv('First loss stage',pretty(r.firstSemanticLossStage))}}${{kv('First loss criterion',pretty(r.firstSemanticLossCriterion))}}${{kv('Batch error',r.batchError)}}</div></div><div class="sec"><h3>Complexity</h3><div class="kvgrid">${{kv('Cyclomatic complexity',r.cyclomaticComplexity)}}${{kv('Decisions',r.decisionCount)}}${{kv('Loops',r.loopCount)}}${{kv('Maximum loop nesting',r.maximumLoopNesting)}}</div></div><div class="sec"><h3>Behavioural evidence</h3><p style="font-size:.82rem;line-height:1.5">${{esc(r.g2Summary||'—')}}</p><p class="muted" style="font-size:.78rem"><strong>Strengths:</strong> ${{esc(r.g2Strengths||'—')}}</p><p class="muted" style="font-size:.78rem"><strong>Limitations:</strong> ${{esc(r.g2Limitations||'—')}}</p></div>`;}}
$('#filter').onchange=()=>{{renderHeat();renderTable()}};$('#labels').onchange=renderHeat;$('#clear').onclick=()=>{{selected=null;renderHeat();$('#detail').innerHTML='<h2>Algorithm inspection</h2><p class="muted">Select a heat-map cell or table row.</p>'}};renderCards();renderHeat();renderTable();
</script></body></html>'''


def generate_batch_dashboard(
    batch_root: Path,
    analysis_directory: Path | None = None,
    output_directory: Path | None = None,
) -> dict[str, Any]:
    batch_root = Path(batch_root)
    analysis_directory = Path(analysis_directory) if analysis_directory else batch_root / "study_analysis"
    dashboard_dir = Path(output_directory) if output_directory else analysis_directory / "dashboards"
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    data = _batch_dashboard_data(batch_root, analysis_directory)
    out = dashboard_dir / "NL_FDEP_batch_dashboard.html"
    out.write_text(_batch_html(data), encoding="utf-8")
    return {
        "status": "GENERATED",
        "dashboard_schema_version": DASHBOARD_SCHEMA_VERSION,
        "dataset": data.get("dataset"),
        "batch_dashboard": str(out.resolve()),
    }


def _discover_completed_llm_batches(study_root: Path) -> list[tuple[Path, Path, dict[str, Any], dict[int, dict[str, Any]]]]:
    found = []
    if not study_root.is_dir():
        return found
    for child in sorted(study_root.iterdir(), key=lambda p: p.name.casefold()):
        if not child.is_dir() or child.name.casefold() == "baseline":
            continue
        results = _results_child(child)
        if results is None:
            continue
        analysis = results / "study_analysis"
        report = _read_json(analysis / "batch_report.json")
        if not isinstance(report, dict) or str(report.get("batch_type") or "").upper() != "LLM_RESULTS":
            continue
        found.append((results, analysis, report, _row_map(analysis)))
    return found


STUDY_DATASET_CONSISTENCY_SCHEMA_VERSION = "1.0"


def update_study_algorithm_count_consistency(study_root: Path) -> dict[str, Any]:
    """Establish and audit the study-level algorithm count N for LLM datasets.

    N is fixed from the first LLM dataset added to the study. The allocation is
    persisted under ``analysis/study_dataset_consistency.json`` so reprocessing a
    later dataset cannot silently redefine the denominator. Subsequent datasets
    are compared with N and, when full ID evidence is available, with the first
    dataset's algorithm-ID set. This is validation metadata only; it does not
    alter scoring or batch artefacts.
    """
    study_root = Path(study_root)
    analysis_root = study_root / "analysis"
    status_path = analysis_root / "study_dataset_consistency.json"
    existing = _read_json(status_path)
    if not isinstance(existing, dict):
        existing = {}

    batches = _discover_completed_llm_batches(study_root)
    batch_info: list[dict[str, Any]] = []
    for results, _analysis, report, rows in batches:
        dataset = str(report.get("dataset") or results.parent.name)
        count = _report_algorithm_count(report, rows)
        ids = _report_algorithm_ids(report, rows)
        batch_info.append({
            "dataset": dataset,
            "results_directory": str(results.resolve()),
            "generated_at_utc": report.get("generated_at_utc"),
            "algorithm_count": count,
            "algorithm_ids": ids,
        })

    expected_count = 0
    try:
        expected_count = max(0, int(existing.get("expected_algorithm_count") or 0))
    except (TypeError, ValueError):
        expected_count = 0
    expected_ids = [int(x) for x in (existing.get("expected_algorithm_ids") or []) if str(x).isdigit() and int(x) > 0]
    reference_dataset = existing.get("reference_dataset")
    reference_results_directory = existing.get("reference_results_directory")

    if expected_count <= 0 and batch_info:
        positive_batches = [item for item in batch_info if int(item.get("algorithm_count") or 0) > 0]
        seed = min(
            positive_batches,
            key=lambda item: (str(item.get("generated_at_utc") or "9999"), str(item.get("dataset") or "").casefold()),
        ) if positive_batches else None
        if seed is not None:
            expected_count = int(seed.get("algorithm_count") or 0)
            expected_ids = list(seed.get("algorithm_ids") or [])
            if expected_count > 0 and len(expected_ids) != expected_count:
                expected_ids = list(range(1, expected_count + 1))
            reference_dataset = seed.get("dataset")
            reference_results_directory = seed.get("results_directory")

    if expected_count > 0 and not expected_ids:
        expected_ids = list(range(1, expected_count + 1))

    expected_set = set(expected_ids)
    dataset_checks = []
    mismatches = []
    for item in sorted(batch_info, key=lambda x: str(x.get("dataset") or "").casefold()):
        actual_count = int(item.get("algorithm_count") or 0)
        actual_ids = list(item.get("algorithm_ids") or [])
        actual_set = set(actual_ids)
        if expected_count <= 0:
            count_match = False
            ids_comparable = False
            missing_ids = []
            extra_ids = []
            id_match = False
            status = "UNESTABLISHED"
        else:
            count_match = actual_count == expected_count
            ids_comparable = bool(expected_set) and len(actual_ids) == actual_count and actual_count > 0
            missing_ids = sorted(expected_set - actual_set) if ids_comparable else []
            extra_ids = sorted(actual_set - expected_set) if ids_comparable else []
            id_match = not missing_ids and not extra_ids
            status = "MATCH" if count_match and id_match else "MISMATCH"
        check = {
            **item,
            "expected_algorithm_count": expected_count,
            "count_match": count_match,
            "id_set_checked": ids_comparable,
            "id_set_match": id_match,
            "missing_algorithm_ids": missing_ids,
            "extra_algorithm_ids": extra_ids,
            "status": status,
        }
        dataset_checks.append(check)
        if status == "MISMATCH":
            mismatches.append(check)

    payload = {
        "schema_version": STUDY_DATASET_CONSISTENCY_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "study_root": str(study_root.resolve()),
        "expected_algorithm_count": expected_count,
        "expected_algorithm_ids": expected_ids,
        "reference_dataset": reference_dataset,
        "reference_results_directory": reference_results_directory,
        "dataset_count": len(dataset_checks),
        "mismatch_count": len(mismatches),
        "status": (
            "NO_VALID_LLM_DATASET" if dataset_checks and expected_count <= 0
            else "MISMATCH" if mismatches
            else "CONSISTENT" if dataset_checks
            else "NO_LLM_DATASETS"
        ),
        "datasets": dataset_checks,
    }
    if dataset_checks:
        analysis_root.mkdir(parents=True, exist_ok=True)
        status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        payload["status_file"] = str(status_path.resolve())
    return payload


def _study_algorithm_design(study_root: Path) -> tuple[int, list[int], dict[str, Any]]:
    consistency = update_study_algorithm_count_consistency(study_root)
    count = int(consistency.get("expected_algorithm_count") or 0)
    ids = [int(x) for x in consistency.get("expected_algorithm_ids") or []]
    if count > 0 and len(ids) != count:
        ids = list(range(1, count + 1))
    return count, ids, consistency


def _study_dashboard_data(study_root: Path) -> dict[str, Any]:
    batches = _discover_completed_llm_batches(study_root)
    expected_count, expected_ids, consistency = _study_algorithm_design(study_root)
    agents = []
    records = []
    for results, analysis, report, rows in batches:
        dataset = str(report.get("dataset") or results.parent.name)
        combined = _combined_behavioural(report)
        live_reviews = [_human_review_record(_algorithm_folder(results, aid), aid) for aid in expected_ids]
        completed_reviews = [r for r in live_reviews if r.get("status") == "COMPLETED"]
        completed_human_scores = [r.get("humanRubric") for r in completed_reviews if _number(r.get("humanRubric")) is not None]
        completed_non_scorable_ids = [
            int(r.get("algorithm"))
            for r in completed_reviews
            if _number(r.get("humanRubric")) is None
            and str(r.get("scoreStatus") or "").upper() == "HUMAN_REVIEW_COMPLETE_NOT_EVALUABLE"
            and r.get("algorithm") is not None
        ]
        completed_unresolved_ids = [
            int(r.get("algorithm"))
            for r in completed_reviews
            if _number(r.get("humanRubric")) is None
            and str(r.get("scoreStatus") or "").upper() != "HUMAN_REVIEW_COMPLETE_NOT_EVALUABLE"
            and r.get("algorithm") is not None
        ]
        completed_unscored_ids = sorted(completed_non_scorable_ids + completed_unresolved_ids)
        human_reviews_completed = len(completed_reviews)
        human_reviews_scored = len(completed_human_scores)
        agents.append({
            "dataset": dataset,
            "meanBehavioural": _number(report.get("mean_experimental_behavioural_percentage")),
            "commonTestAccuracy": _number(report.get("semantic_test_accuracy_percentage")),
            "combinedBehavioural": combined,
            "boundaryVariance": _number(report.get("semantic_boundary_variance_percentage")),
            "meanAutomatedRubric": _mean([r.get("AutomatedRubricPercent") for r in rows.values()]),
            # Descriptive presentation statistic only. Partial review values may be
            # visible elsewhere, but they are never eligible for Final Scoring.
            "meanHumanRubric": _mean([r.get("humanRubric") for r in live_reviews]),
            "meanCompletedHumanRubric": _mean(completed_human_scores),
            "meanCombinedRubric": _mean([r.get("combinedRubric") for r in live_reviews if r.get("combinedAvailable")]),
            "meanHumanAgreement": _mean([r.get("agreementPercentage") for r in live_reviews]),
            "humanReviewsCompleted": human_reviews_completed,
            "humanReviewsScored": human_reviews_scored,
            "humanReviewsCompletedWithoutScore": len(completed_unscored_ids),
            "humanReviewsCompletedWithoutScoreIds": completed_unscored_ids,
            "humanReviewsCompletedNonScorable": len(completed_non_scorable_ids),
            "humanReviewsCompletedNonScorableIds": completed_non_scorable_ids,
            "humanReviewsCompletedUnresolvedMissingScore": len(completed_unresolved_ids),
            "humanReviewsCompletedUnresolvedMissingScoreIds": completed_unresolved_ids,
            "humanReviewsRequired": expected_count,
            "pipelineStatusCounts": report.get("pipeline_status_counts") or report.get("status_counts") or {},
            "comparisonCounts": report.get("comparison_to_baseline_counts") or {},
            "semanticTestsEvaluable": report.get("semantic_tests_evaluable"),
            "semanticTestsPassed": report.get("semantic_tests_passed"),
        })
        batch_records = _batch_records(report)
        for aid in expected_ids:
            row = rows.get(aid, {})
            rec = batch_records.get(aid, {})
            records.append({
                "dataset": dataset,
                "algorithm": aid,
                "score": _number(row.get("ExperimentalBehaviouralPercent") if row else rec.get("experimental_behavioural_percentage")),
                "comparison": row.get("ComparisonToBaseline") if row else rec.get("comparison_to_baseline"),
                "pipelineStatus": row.get("PipelineStatus") if row else rec.get("status"),
                "boundaryVariance": _number(row.get("SemanticBoundaryVariancePercent") if row else rec.get("semantic_boundary_variance_percentage")),
                "automatedRubric": _number(row.get("AutomatedRubricPercent")),
                "humanRubric": _number(row.get("HumanRubricPercent")),
                "combinedRubric": _number(row.get("CombinedRubricPercent")),
                "combinedRubricAvailable": bool(row.get("CombinedRubricAvailable")),
            })
    agents.sort(key=lambda x: (-(x.get("combinedBehavioural") if x.get("combinedBehavioural") is not None else -1), x["dataset"].casefold()))
    order = [a["dataset"] for a in agents]
    return {
        "schemaVersion": DASHBOARD_SCHEMA_VERSION,
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "studyRoot": str(study_root.resolve()),
        "algorithmCount": expected_count,
        "algorithmIds": expected_ids,
        "datasetConsistency": consistency,
        "agents": agents,
        "agentOrder": order,
        "records": records,
    }


def _human_review_study_data(study_root: Path) -> dict[str, Any]:
    # Aggregate existing human-review artefacts for presentation-only analysis.
    study_root = Path(study_root)
    expected_count, expected_ids, _consistency = _study_algorithm_design(study_root)
    batch_specs: list[tuple[str, str, Path, list[int]]] = []
    for results, _analysis, report, _rows in _discover_completed_llm_batches(study_root):
        batch_specs.append((str(report.get("dataset") or results.parent.name), "LLM_RESULTS", results, expected_ids))

    baseline = study_root / "Baseline"
    baseline_analysis = baseline / "study_analysis"
    baseline_report = _read_json(baseline_analysis / "batch_report.json")
    if isinstance(baseline_report, dict) and str(baseline_report.get("batch_type") or "").upper() == "BASELINE":
        pseudo = baseline / "pseudocode"
        baseline_ids = _report_algorithm_ids(baseline_report, _row_map(baseline_analysis))
        batch_specs.append((str(baseline_report.get("dataset") or "Baseline"), "BASELINE", pseudo if pseudo.is_dir() else baseline, baseline_ids))

    records: list[dict[str, Any]] = []
    for dataset, batch_type, batch_root, algorithm_ids in batch_specs:
        for aid in algorithm_ids:
            folder = _algorithm_folder(batch_root, aid)
            review = _human_review_record(folder, aid)
            records.append({"dataset": dataset, "batchType": batch_type, **review})

    datasets: list[dict[str, Any]] = []
    for dataset, batch_type, _root, _algorithm_ids in batch_specs:
        items = [r for r in records if r["dataset"] == dataset and r["batchType"] == batch_type]
        datasets.append({
            "dataset": dataset,
            "batchType": batch_type,
            "algorithmCount": len(items),
            "reviewsPresent": sum(1 for r in items if r.get("reviewPresent")),
            "reviewsCompleted": sum(1 for r in items if r.get("status") == "COMPLETED"),
            "reviewsPartial": sum(1 for r in items if r.get("status") in {"PARTIAL", "EMPTY"}),
            "reviewsPending": sum(1 for r in items if r.get("status") == "PENDING"),
            "criteriaCompleted": sum(int(r.get("criteriaCompleted") or 0) for r in items),
            "criteriaTotal": sum(int(r.get("criteriaTotal") or 0) for r in items),
            "meanHumanRubric": _mean([r.get("humanRubric") for r in items]),
            "meanCombinedRubric": _mean([r.get("combinedRubric") for r in items if r.get("combinedAvailable")]),
            "meanAgreement": _mean([r.get("agreementPercentage") for r in items]),
            "semanticIssues": sum(int(r.get("semanticIssueCount") or 0) for r in items),
        })

    reviewer_map: dict[str, dict[str, Any]] = {}
    for r in records:
        rv = r.get("reviewer") or {}
        rid = str(rv.get("reviewerId") or "").strip()
        name = str(rv.get("reviewerName") or "").strip()
        if not rid and not name:
            continue
        key = rid or f"NAME:{name}"
        item = reviewer_map.setdefault(key, {
            "reviewerId": rid or None,
            "reviewerName": name or None,
            "reviews": 0,
            "completed": 0,
            "partial": 0,
            "datasets": set(),
            "humanRubrics": [],
            "agreements": [],
            "confidenceCounts": {},
            "semanticIssues": 0,
        })
        item["reviews"] += 1
        if r.get("status") == "COMPLETED": item["completed"] += 1
        elif r.get("status") in {"PARTIAL", "EMPTY"}: item["partial"] += 1
        item["datasets"].add(r.get("dataset"))
        if _number(r.get("humanRubric")) is not None: item["humanRubrics"].append(r.get("humanRubric"))
        if _number(r.get("agreementPercentage")) is not None: item["agreements"].append(r.get("agreementPercentage"))
        confidence = str(rv.get("confidence") or "").strip()
        if confidence: item["confidenceCounts"][confidence] = item["confidenceCounts"].get(confidence, 0) + 1
        item["semanticIssues"] += int(r.get("semanticIssueCount") or 0)

    reviewers = []
    for item in reviewer_map.values():
        reviewers.append({
            "reviewerId": item["reviewerId"],
            "reviewerName": item["reviewerName"],
            "reviews": item["reviews"],
            "completed": item["completed"],
            "partial": item["partial"],
            "datasets": sorted(str(x) for x in item["datasets"] if x),
            "meanHumanRubric": _mean(item["humanRubrics"]),
            "meanAgreement": _mean(item["agreements"]),
            "confidenceCounts": item["confidenceCounts"],
            "semanticIssues": item["semanticIssues"],
        })
    reviewers.sort(key=lambda x: (str(x.get("reviewerId") or "").casefold(), str(x.get("reviewerName") or "").casefold()))

    criterion_map: dict[str, dict[str, Any]] = {}
    agreement_counts: dict[str, int] = {}
    for r in records:
        for c in r.get("criteria") or []:
            if not c.get("humanCompleted"):
                continue
            cid = str(c.get("criterionId") or "")
            if not cid:
                continue
            item = criterion_map.setdefault(cid, {
                "criterionId": cid,
                "stageName": c.get("stageName") or c.get("stageKey"),
                "question": c.get("question"),
                "completed": 0,
                "numericScores": [],
                "agreementCounts": {},
                "semanticIssues": 0,
            })
            item["completed"] += 1
            if _number(c.get("humanScore")) is not None: item["numericScores"].append(c.get("humanScore"))
            ag = str(c.get("agreement") or "").strip()
            if ag:
                item["agreementCounts"][ag] = item["agreementCounts"].get(ag, 0) + 1
                agreement_counts[ag] = agreement_counts.get(ag, 0) + 1
            if c.get("semanticIssue") is True: item["semanticIssues"] += 1

    criteria = []
    for item in criterion_map.values():
        ag_total = sum(item["agreementCounts"].values())
        agree = item["agreementCounts"].get("AGREE", 0)
        criteria.append({
            "criterionId": item["criterionId"],
            "stageName": item["stageName"],
            "question": item["question"],
            "completed": item["completed"],
            "meanHumanScore": _mean(item["numericScores"]),
            "agreementCounts": item["agreementCounts"],
            "agreementPercentage": round(agree / ag_total * 100, 2) if ag_total else None,
            "semanticIssues": item["semanticIssues"],
        })
    criteria.sort(key=lambda x: x["criterionId"])

    completion_counts = {
        "COMPLETED": sum(1 for r in records if r.get("status") == "COMPLETED"),
        "PARTIAL": sum(1 for r in records if r.get("status") in {"PARTIAL", "EMPTY"}),
        "PENDING": sum(1 for r in records if r.get("status") == "PENDING"),
    }
    return {
        "schemaVersion": DASHBOARD_SCHEMA_VERSION,
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "studyRoot": str(study_root.resolve()),
        "datasets": datasets,
        "reviewers": reviewers,
        "criteria": criteria,
        "records": records,
        "completionCounts": completion_counts,
        "agreementCounts": agreement_counts,
        "summary": {
            "algorithmInstances": len(records),
            "reviewsPresent": sum(1 for r in records if r.get("reviewPresent")),
            "reviewsCompleted": completion_counts["COMPLETED"],
            "reviewsPartial": completion_counts["PARTIAL"],
            "reviewsPending": completion_counts["PENDING"],
            "criteriaCompleted": sum(int(r.get("criteriaCompleted") or 0) for r in records),
            "criteriaTotal": sum(int(r.get("criteriaTotal") or 0) for r in records),
            "meanHumanRubric": _mean([r.get("humanRubric") for r in records]),
            "meanCombinedRubric": _mean([r.get("combinedRubric") for r in records if r.get("combinedAvailable")]),
            "meanAgreement": _mean([r.get("agreementPercentage") for r in records]),
            "reviewerCount": len(reviewers),
            "semanticIssues": sum(int(r.get("semanticIssueCount") or 0) for r in records),
        },
    }


def _human_review_html(data: dict[str, Any]) -> str:
    j = _safe_json_for_script(data)
    return f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NL-FDEP Combined Human Review Dashboard</title><style>{_COMMON_CSS}
.reviewgrid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:16px;margin-bottom:16px}}.donutrow{{display:flex;gap:18px;align-items:center;flex-wrap:wrap}}.donut{{width:145px;height:145px;border-radius:50%;position:relative;flex:0 0 auto}}.donut:after{{content:"";position:absolute;inset:27px;background:#fff;border-radius:50%;border:1px solid var(--border)}}.donutlabel{{font-size:.8rem;line-height:1.7}}.tiny{{font-size:.73rem;color:var(--muted)}}.review-layout{{display:grid;grid-template-columns:minmax(0,1fr) 460px;gap:16px;align-items:start}}.review-detail{{position:sticky;top:12px;max-height:calc(100vh - 24px);overflow:auto;padding:16px}}@media(max-width:1100px){{.review-layout{{grid-template-columns:1fr}}.review-detail{{position:static;max-height:none}}}}</style></head><body><div class="page"><h1>NL-FDEP Combined Human Review Dashboard</h1><p class="sub">Read-only analysis of saved human-review and adjudication artefacts across completed study batches. No values shown here participate in scoring or adjudication.</p><div id="cards" class="cards"></div>
<div class="reviewgrid"><div class="panel" style="padding:16px"><h2 style="margin-top:0;font-size:1.05rem">Review completion</h2><div class="donutrow"><div id="completionDonut" class="donut"></div><div id="completionLegend" class="donutlabel"></div></div></div><div class="panel" style="padding:16px"><h2 style="margin-top:0;font-size:1.05rem">Criterion agreement</h2><div class="donutrow"><div id="agreementDonut" class="donut"></div><div id="agreementLegend" class="donutlabel"></div></div></div></div>
<div class="panel" style="padding:14px;margin-bottom:16px"><h2 style="margin-top:0;font-size:1.05rem">Dataset review summary</h2><div class="tablewrap"><table class="rank"><thead><tr><th>Dataset</th><th>Type</th><th>Complete</th><th>Partial</th><th>Pending</th><th>Criteria</th><th>Mean human rubric</th><th>Mean agreement</th><th>Semantic issues</th></tr></thead><tbody id="datasetRows"></tbody></table></div></div>
<div class="panel" style="padding:14px;margin-bottom:16px"><h2 style="margin-top:0;font-size:1.05rem">Reviewer summary</h2><div class="tablewrap"><table class="rank"><thead><tr><th>Reviewer</th><th>Name</th><th>Reviews</th><th>Complete</th><th>Partial</th><th>Datasets</th><th>Mean human rubric</th><th>Mean agreement</th><th>Semantic issues</th></tr></thead><tbody id="reviewerRows"></tbody></table></div></div>
<div class="panel" style="padding:14px;margin-bottom:16px"><h2 style="margin-top:0;font-size:1.05rem">Criterion-level human review analysis</h2><div class="tablewrap"><table class="rank"><thead><tr><th>Criterion</th><th>Stage</th><th>Completed</th><th>Mean human score</th><th>Agreement</th><th>Semantic issues</th><th>Question</th></tr></thead><tbody id="criterionRows"></tbody></table></div></div>
<div class="toolbar panel"><strong>Review records</strong><select id="datasetFilter"><option value="">All datasets</option></select><select id="reviewerFilter"><option value="">All reviewers</option></select><select id="statusFilter"><option value="">All statuses</option><option>COMPLETED</option><option>PARTIAL</option><option>EMPTY</option><option>PENDING</option></select><button id="clearReview">Clear selection</button></div>
<div class="review-layout"><div class="panel" style="padding:14px"><div class="tablewrap"><table class="rank"><thead><tr><th>Dataset</th><th>Alg.</th><th>Status</th><th>Reviewer</th><th>Confidence</th><th>Criteria</th><th>Human rubric</th><th>Agreement</th><th>Semantic issues</th></tr></thead><tbody id="reviewRows"></tbody></table></div></div><div id="reviewDetail" class="panel review-detail"><h2>Human review inspection</h2><p class="muted">Select a review record to inspect its saved assessments and justifications.</p></div></div>
</div><script>const DATA={j};const $=s=>document.querySelector(s);const esc=v=>String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;');const pct=v=>v==null||Number.isNaN(+v)?'—':(+v).toFixed(2)+'%';const pretty=v=>v==null||v===''?'—':String(v).replaceAll('_',' ');const score=v=>v==null?'—':String(v);
function card(k,v){{return `<div class="panel card"><div class="k">${{esc(k)}}</div><div class="v">${{esc(v)}}</div></div>`}}function kv(k,v){{return `<div class="kv"><div class="k">${{esc(k)}}</div><div class="v">${{esc(v??'—')}}</div></div>`}}
const S=DATA.summary;$('#cards').innerHTML=[card('Algorithm instances',S.algorithmInstances),card('Human reviews present',S.reviewsPresent),card('Reviews completed',S.reviewsCompleted),card('Reviews partial',S.reviewsPartial),card('Reviews pending',S.reviewsPending),card('Reviewers',S.reviewerCount),card('Mean Human Rubric',pct(S.meanHumanRubric)),card('Mean human/auto agreement',pct(S.meanAgreement)),card('Semantic issues marked',S.semanticIssues)].join('');
function donut(el,counts,items){{const total=items.reduce((n,x)=>n+(counts[x.key]||0),0)||1;let at=0,parts=[];for(const x of items){{const n=counts[x.key]||0,p=n/total*100;parts.push(`${{x.colour}} ${{at}}% ${{at+p}}%`);at+=p}}el.style.background=`conic-gradient(${{parts.join(',')}})`;return items.map(x=>`<div><i class="sw" style="background:${{x.colour}}"></i>${{esc(x.label)}}: <strong>${{counts[x.key]||0}}</strong></div>`).join('')}}
$('#completionLegend').innerHTML=donut($('#completionDonut'),DATA.completionCounts,[{{key:'COMPLETED',label:'Completed',colour:'#2ca25f'}},{{key:'PARTIAL',label:'Partial',colour:'#ffc145'}},{{key:'PENDING',label:'Pending',colour:'#d9e0ea'}}]);$('#agreementLegend').innerHTML=donut($('#agreementDonut'),DATA.agreementCounts,[{{key:'AGREE',label:'Agree',colour:'#2ca25f'}},{{key:'PARTIALLY_AGREE',label:'Partially agree',colour:'#ffc145'}},{{key:'DISAGREE',label:'Disagree',colour:'#d95f59'}}]);
$('#datasetRows').innerHTML=DATA.datasets.map(d=>`<tr><td><strong>${{esc(d.dataset)}}</strong></td><td>${{pretty(d.batchType)}}</td><td class="num">${{d.reviewsCompleted}}</td><td class="num">${{d.reviewsPartial}}</td><td class="num">${{d.reviewsPending}}</td><td class="num">${{d.criteriaCompleted}} / ${{d.criteriaTotal}}</td><td class="num">${{pct(d.meanHumanRubric)}}</td><td class="num">${{pct(d.meanAgreement)}}</td><td class="num">${{d.semanticIssues}}</td></tr>`).join('');
$('#reviewerRows').innerHTML=DATA.reviewers.map(r=>`<tr><td><strong>${{esc(r.reviewerId||'—')}}</strong></td><td>${{esc(r.reviewerName||'—')}}</td><td class="num">${{r.reviews}}</td><td class="num">${{r.completed}}</td><td class="num">${{r.partial}}</td><td>${{esc((r.datasets||[]).join(', '))}}</td><td class="num">${{pct(r.meanHumanRubric)}}</td><td class="num">${{pct(r.meanAgreement)}}</td><td class="num">${{r.semanticIssues}}</td></tr>`).join('');
$('#criterionRows').innerHTML=DATA.criteria.map(c=>`<tr><td><strong>${{esc(c.criterionId)}}</strong></td><td>${{esc(c.stageName||'—')}}</td><td class="num">${{c.completed}}</td><td class="num">${{c.meanHumanScore==null?'—':(+c.meanHumanScore).toFixed(2)}}</td><td class="num">${{pct(c.agreementPercentage)}}</td><td class="num">${{c.semanticIssues}}</td><td>${{esc(c.question||'—')}}</td></tr>`).join('');
const datasets=[...new Set(DATA.records.map(r=>r.dataset))].sort();$('#datasetFilter').innerHTML+=datasets.map(x=>`<option>${{esc(x)}}</option>`).join('');const reviewers=[...new Set(DATA.records.map(r=>(r.reviewer||{{}}).reviewerId).filter(Boolean))].sort();$('#reviewerFilter').innerHTML+=reviewers.map(x=>`<option>${{esc(x)}}</option>`).join('');
function visible(r){{const d=$('#datasetFilter').value,u=$('#reviewerFilter').value,s=$('#statusFilter').value;return (!d||r.dataset===d)&&(!u||(r.reviewer||{{}}).reviewerId===u)&&(!s||r.status===s)}}
function renderRecords(){{$('#reviewRows').innerHTML=DATA.records.filter(visible).map(r=>{{const rv=r.reviewer||{{}};return `<tr data-dataset="${{esc(r.dataset)}}" data-alg="${{r.algorithm}}" style="cursor:pointer"><td>${{esc(r.dataset)}}</td><td>${{r.algorithm}}</td><td>${{pretty(r.status)}}</td><td>${{esc(rv.reviewerId||rv.reviewerName||'—')}}</td><td>${{pretty(rv.confidence)}}</td><td class="num">${{r.criteriaCompleted}} / ${{r.criteriaTotal}}</td><td class="num">${{pct(r.humanRubric)}}</td><td class="num">${{pct(r.agreementPercentage)}}</td><td class="num">${{r.semanticIssueCount}}</td></tr>`}}).join('');document.querySelectorAll('#reviewRows tr').forEach(tr=>tr.onclick=()=>selectReview(tr.dataset.dataset,+tr.dataset.alg))}}
function criterionTable(r){{const rows=(r.criteria||[]).map(c=>`<tr><td><strong>${{esc(c.criterionId||'—')}}</strong></td><td>${{esc(c.question||'—')}}</td><td class="num">${{c.automatedScore??'—'}}</td><td class="num">${{c.humanCompleted?(c.humanScoreLabel??c.humanScore??'—'):'—'}}</td><td>${{pretty(c.agreement)}}</td><td>${{c.semanticIssue===true?'Yes':c.semanticIssue===false?'No':'—'}}</td><td>${{esc(c.reviewerJustification||'—')}}</td></tr>`).join('');return `<div class="tablewrap"><table class="rank"><thead><tr><th>Criterion</th><th>Question</th><th>Auto</th><th>Human</th><th>Agreement</th><th>Issue</th><th>Justification</th></tr></thead><tbody>${{rows||'<tr><td colspan="7">No human criterion assessments.</td></tr>'}}</tbody></table></div>`}}
function selectReview(dataset,alg){{const r=DATA.records.find(x=>x.dataset===dataset&&x.algorithm===alg);if(!r)return;const rv=r.reviewer||{{}},ss=r.sourceSufficiency||{{}},g2=r.behaviouralEvidenceAdequacy||{{}},ts=r.taskSemanticEvaluation||{{}},ov=r.overallReview||{{}};$('#reviewDetail').innerHTML=`<h2>${{esc(dataset)}} · Algorithm ${{alg}}</h2><p class="muted">${{pretty(r.status)}} · ${{r.criteriaCompleted}} / ${{r.criteriaTotal}} human criteria completed</p><div class="sec"><h3>Reviewer</h3><div class="kvgrid">${{kv('Reviewer ID',rv.reviewerId)}}${{kv('Reviewer name',rv.reviewerName)}}${{kv('Reviewed at UTC',rv.reviewedAtUtc)}}${{kv('Confidence',rv.confidence)}}${{kv('Human rubric',pct(r.humanRubric))}}${{kv('Combined rubric',r.combinedAvailable?pct(r.combinedRubric):'—')}}${{kv('Automated/human agreement',pct(r.agreementPercentage))}}${{kv('Semantic issues marked',r.semanticIssueCount)}}</div></div><div class="sec"><h3>Review gates</h3><div class="kvgrid">${{kv('Source sufficiency — automated',pretty(ss.automatedResult))}}${{kv('Source sufficiency — human',pretty(ss.humanResult))}}${{kv('Source agreement',pretty(ss.agreement))}}${{kv('Behavioural evidence — automated',pretty(g2.automatedResult))}}${{kv('Behavioural evidence — human',pretty(g2.humanResult))}}${{kv('Behavioural evidence agreement',pretty(g2.agreement))}}</div><p class="tiny"><strong>Source justification:</strong> ${{esc(ss.reviewerJustification||'—')}}</p><p class="tiny"><strong>Evidence justification:</strong> ${{esc(g2.reviewerJustification||'—')}}</p></div><div class="sec"><h3>Task-semantic human assessment</h3><div class="kvgrid">${{kv('Required inputs represented',pretty(ts.required_inputs_represented))}}${{kv('Core algorithm logic',pretty(ts.core_algorithm_logic))}}${{kv('Required output semantics',pretty(ts.required_output_semantics_represented))}}${{kv('Edge/domain handling',pretty(ts.edge_and_domain_handling))}}${{kv('Overall semantic assessment',pretty(ts.overall_semantic_assessment))}}</div><p class="tiny"><strong>Reviewer justification:</strong> ${{esc(ts.reviewer_justification||'—')}}</p></div><div class="sec"><h3>Overall review</h3><div class="kvgrid">${{kv('Material semantic error not captured',pretty(ov.material_semantic_error_not_captured))}}${{kv('First semantic loss stage',pretty(ov.first_semantic_loss_stage))}}${{kv('Final Python behaviourally faithful',pretty(ov.final_python_behaviourally_faithful))}}</div><p class="tiny"><strong>Additional observations:</strong> ${{esc(ov.additional_observations||'—')}}</p></div><div class="sec"><h3>Criterion-level review</h3>${{criterionTable(r)}}</div>`}}
['#datasetFilter','#reviewerFilter','#statusFilter'].forEach(sel=>$(sel).onchange=renderRecords);$('#clearReview').onclick=()=>{{$('#datasetFilter').value='';$('#reviewerFilter').value='';$('#statusFilter').value='';renderRecords();$('#reviewDetail').innerHTML='<h2>Human review inspection</h2><p class="muted">Select a review record to inspect its saved assessments and justifications.</p>'}};renderRecords();
</script></body></html>'''


def generate_human_review_dashboard(study_root: Path, output_directory: Path | None = None) -> dict[str, Any]:
    study_root = Path(study_root)
    data = _human_review_study_data(study_root)
    output_directory = Path(output_directory) if output_directory else study_root / "analysis" / "dashboards"
    output_directory.mkdir(parents=True, exist_ok=True)
    out = output_directory / "NL_FDEP_human_review_dashboard.html"
    out.write_text(_human_review_html(data), encoding="utf-8")
    return {
        "status": "GENERATED",
        "dashboard_schema_version": DASHBOARD_SCHEMA_VERSION,
        "human_review_dashboard": str(out.resolve()),
        "review_record_count": len(data.get("records") or []),
        "reviewer_count": len(data.get("reviewers") or []),
    }


def _study_html(data: dict[str, Any]) -> str:
    """Render one comparative page with heat-map and clickable pie-chart tabs."""
    j = _safe_json_for_script(data)
    template = r'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NL-FDEP Comparative Study Dashboard</title><style>__COMMON_CSS__
.studyrow{display:grid;grid-template-columns:230px minmax(0,1fr);gap:10px;align-items:center;margin:5px 0}.agentname{font-size:.8rem;font-weight:750;overflow-wrap:anywhere}.viewtabs{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:10px 12px;margin-bottom:16px}.viewtab[aria-selected="true"]{background:var(--accent);color:#fff;border-color:var(--accent)}.compare-layout{display:grid;grid-template-columns:minmax(0,1fr) 390px;gap:16px;align-items:start}.compare-detail{padding:16px;position:sticky;top:12px}.viewpanel[hidden]{display:none}.average-agent{padding:14px;margin:0 0 14px}.average-agent h3{margin:0 0 4px;font-size:1rem}.average-agent .agentmeta{font-size:.76rem;color:var(--muted);margin-bottom:12px}.average-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(132px,1fr));gap:12px}.avgpie{appearance:none;background:#fff;border:1px solid var(--border);border-radius:10px;padding:10px 8px;cursor:pointer;text-align:center;color:inherit;min-width:0}.avgpie:hover,.avgpie.sel{outline:2px solid #172033;outline-offset:1px}.avgpie-circle{display:block;width:82px;height:82px;border-radius:50%;margin:0 auto 8px;position:relative;border:1px solid rgba(0,0,0,.16);background:conic-gradient(var(--pie-colour) calc(var(--score) * 1%),#edf1f6 0)}.avgpie-circle:after{content:"";position:absolute;inset:17px;background:#fff;border-radius:50%;border:1px solid var(--border)}.avgpie.ne .avgpie-circle{background:#fff;border-style:dashed}.avgpie-value{display:block;font-size:.95rem;font-weight:800;line-height:1.2}.avgpie-label{display:block;font-size:.72rem;color:var(--muted);line-height:1.25;margin-top:3px}.detail-note{font-size:.78rem;color:var(--muted);line-height:1.5}.rankpanel{margin-top:16px;padding:14px}@media(max-width:1050px){.compare-layout{grid-template-columns:1fr}.compare-detail{position:static}}@media(max-width:800px){.studyrow{grid-template-columns:130px minmax(0,1fr)}}
</style></head><body><div class="page"><h1>NL-FDEP Comparative Study Dashboard</h1><p class="sub">Heat map = per-algorithm behavioural results. Pie charts = overall agent averages and aggregate study measures. Baseline results are not included as an experimental agent row.</p><div id="cards" class="cards"></div>
<div class="panel viewtabs" role="tablist" aria-label="Comparative visualisation"><strong>View</strong><button type="button" class="viewtab" id="heatTab" role="tab" aria-controls="heatView" aria-selected="true">Heat map</button><button type="button" class="viewtab" id="pieTab" role="tab" aria-controls="pieView" aria-selected="false">Pie charts</button><button type="button" id="clearSelection">Clear selection</button></div>
<div class="compare-layout"><div><section id="heatView" class="viewpanel panel heat-wrap" role="tabpanel" aria-labelledby="heatTab"><h2 style="margin:0 0 4px;font-size:1.05rem">Comparative 50-algorithm behavioural heat map</h2><p class="muted" style="font-size:.8rem;margin-top:0">All 50 algorithms remain visible for every completed agent. White = not evaluable / no behavioural score. Select any cell for details.</p><div id="heatRows"></div><div class="legend"><strong>Behavioural score:</strong><span><i class="sw" style="background:#2f6db3"></i>0</span><span><i class="sw" style="background:#6ec5ff"></i>25</span><span><i class="sw" style="background:#ffc145"></i>50</span><span><i class="sw" style="background:#9be564"></i>75</span><span><i class="sw" style="background:#2ca25f"></i>100</span><span><i class="sw" style="background:#fff"></i>Not evaluable</span></div></section>
<section id="pieView" class="viewpanel" role="tabpanel" aria-labelledby="pieTab" hidden><div class="panel heat-wrap"><h2 style="margin:0 0 4px;font-size:1.05rem">Overall agent averages</h2><p class="muted" style="font-size:.8rem;margin-top:0">Agent-level averages and aggregate study measures only. Per-algorithm percentages remain in the Heat map tab. Select any donut for its stored value and agent summary.</p></div><div id="pieRows"></div></section>
<div class="panel rankpanel"><h2 style="margin-top:0;font-size:1.05rem">Behavioural ranking</h2><div class="tablewrap"><table class="rank"><thead><tr><th>Rank</th><th>AI agent</th><th>Mean semantic behavioural</th><th>Common Test accuracy</th><th>Combined Behavioural Measure</th><th>Semantic Boundary Variance</th><th>Mean Human Rubric</th><th>Mean Human/Auto Agreement</th><th>Mean Combined Rubric</th></tr></thead><tbody id="rank"></tbody></table></div></div></div>
<aside class="panel compare-detail" id="compareDetail"><h2>Comparative inspection</h2><p class="muted">Select a heat-map cell for an algorithm result, or an overall pie for an agent-level metric.</p></aside></div>
</div><script>const DATA=__DATA__;const $=s=>document.querySelector(s);const esc=v=>String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;');const pct=v=>v==null||Number.isNaN(+v)?'—':(+v).toFixed(2)+'%';const pretty=v=>v==null||v===''?'—':String(v).replaceAll('_',' ');let selectedKey=null;
function colour(v){if(v==null)return '#fff';const s=[[0,[47,109,179]],[25,[110,197,255]],[50,[255,193,69]],[75,[155,229,100]],[100,[44,162,95]]];v=Math.max(0,Math.min(100,+v));for(let i=1;i<s.length;i++)if(v<=s[i][0]){const [x0,c0]=s[i-1],[x1,c1]=s[i],t=(v-x0)/(x1-x0),c=c0.map((q,j)=>Math.round(q+(c1[j]-q)*t));return `rgb(${c[0]},${c[1]},${c[2]})`}return '#2ca25f'}
function key(r){return `${r.dataset}|${r.algorithm}`}
function kv(k,v){return `<div class="kv"><div class="k">${esc(k)}</div><div class="v">${esc(v??'—')}</div></div>`}
const total=DATA.agents.length*50,evals=DATA.records.filter(r=>r.score!=null).length,at=DATA.records.filter(r=>r.comparison==='AT_REFERENCE').length,below=DATA.records.filter(r=>r.comparison==='BELOW_REFERENCE').length;$('#cards').innerHTML=`<div class="panel card"><div class="k">Completed agents</div><div class="v">${DATA.agents.length}</div></div><div class="panel card"><div class="k">Algorithm instances</div><div class="v">${total}</div></div><div class="panel card"><div class="k">Behaviourally evaluable</div><div class="v">${evals}</div></div><div class="panel card"><div class="k">At reference</div><div class="v">${at}</div></div><div class="panel card"><div class="k">Below reference</div><div class="v">${below}</div></div>`;
const grouped=new Map(DATA.agentOrder.map(n=>[n,DATA.records.filter(r=>r.dataset===n)]));
const AVG_METRICS=[
 {key:'meanBehavioural',label:'Mean semantic behavioural'},
 {key:'commonTestAccuracy',label:'Common Test accuracy'},
 {key:'combinedBehavioural',label:'Combined Behavioural Measure'},
 {key:'boundaryVariance',label:'Semantic Boundary Variance'},
 {key:'meanAutomatedRubric',label:'Mean Automated Rubric'},
 {key:'meanHumanRubric',label:'Mean Human Rubric'},
 {key:'meanHumanAgreement',label:'Mean Human/Auto Agreement'},
 {key:'meanCombinedRubric',label:'Mean Combined Rubric'}
];
function renderHeat(){const rows=DATA.agentOrder.map(name=>`<div class="studyrow"><div class="agentname">${esc(name)}</div><div class="heat-row">${grouped.get(name).map(r=>`<button type="button" class="cell ${r.algorithm%5===0?'sep ':''}${selectedKey===`alg:${key(r)}`?'sel':''}" data-dataset="${esc(name)}" data-alg="${r.algorithm}" aria-label="${esc(name)} Algorithm ${r.algorithm}: ${pct(r.score)}" title="${esc(name)} · Algorithm ${r.algorithm} · ${pct(r.score)}" style="background:${colour(r.score)}"></button>`).join('')}</div></div>`).join('');$('#heatRows').innerHTML=rows;document.querySelectorAll('#heatRows .cell').forEach(x=>x.addEventListener('click',()=>selectRecord(x.dataset.dataset,+x.dataset.alg)))}
function renderPies(){
 const rows=DATA.agentOrder.map(name=>{const a=DATA.agents.find(x=>x.dataset===name)||{};const completed=a.humanReviewsCompleted??0;return `<section class="panel average-agent"><h3>${esc(name)}</h3><div class="agentmeta">Human reviews completed: ${completed} / 50</div><div class="average-grid">${AVG_METRICS.map(m=>{const raw=a[m.key],ne=raw==null||Number.isNaN(+raw),score=ne?0:Math.max(0,Math.min(100,+raw)),sk=`avg:${name}|${m.key}`;return `<button type="button" class="avgpie ${ne?'ne ':''}${selectedKey===sk?'sel':''}" data-dataset="${esc(name)}" data-metric="${m.key}" aria-label="${esc(name)} ${esc(m.label)}: ${pct(raw)}" title="${esc(name)} · ${esc(m.label)} · ${pct(raw)}" style="--score:${score};--pie-colour:${ne?'#fff':colour(score)}"><span class="avgpie-circle" aria-hidden="true"></span><span class="avgpie-value">${pct(raw)}</span><span class="avgpie-label">${esc(m.label)}</span></button>`}).join('')}</div></section>`}).join('');
 $('#pieRows').innerHTML=rows;document.querySelectorAll('#pieRows .avgpie').forEach(x=>x.addEventListener('click',()=>selectAverage(x.dataset.dataset,x.dataset.metric)))
}
function renderRank(){$('#rank').innerHTML=DATA.agents.map((a,i)=>`<tr><td>${i+1}</td><td><strong>${esc(a.dataset)}</strong></td><td class="num">${pct(a.meanBehavioural)}</td><td class="num">${pct(a.commonTestAccuracy)}</td><td class="num"><strong>${pct(a.combinedBehavioural)}</strong></td><td class="num">${pct(a.boundaryVariance)}</td><td class="num">${pct(a.meanHumanRubric)}</td><td class="num">${pct(a.meanHumanAgreement)}</td><td class="num">${pct(a.meanCombinedRubric)}</td></tr>`).join('')}
function selectRecord(dataset,algorithm){const r=DATA.records.find(x=>x.dataset===dataset&&x.algorithm===algorithm);if(!r)return;selectedKey=`alg:${key(r)}`;renderHeat();renderPies();const agent=DATA.agents.find(x=>x.dataset===dataset)||{};$('#compareDetail').innerHTML=`<h2>${esc(dataset)} · Algorithm ${algorithm}</h2><p class="muted">${pretty(r.pipelineStatus)}</p><div class="sec"><h3>Algorithm result</h3><div class="kvgrid">${kv('Behavioural score',pct(r.score))}${kv('Reference comparison',pretty(r.comparison))}${kv('Semantic Boundary Variance',pct(r.boundaryVariance))}${kv('Automated rubric',pct(r.automatedRubric))}${kv('Human rubric',pct(r.humanRubric))}${kv('Combined rubric',r.combinedRubricAvailable?pct(r.combinedRubric):'—')}</div></div><div class="sec"><h3>Agent summary</h3><div class="kvgrid">${kv('Mean semantic behavioural',pct(agent.meanBehavioural))}${kv('Common Test accuracy',pct(agent.commonTestAccuracy))}${kv('Combined Behavioural Measure',pct(agent.combinedBehavioural))}${kv('Mean Human Rubric',pct(agent.meanHumanRubric))}${kv('Mean Human/Auto Agreement',pct(agent.meanHumanAgreement))}${kv('Human reviews completed',`${agent.humanReviewsCompleted??0} / 50`)}</div></div><p class="detail-note">The Heat map shows per-algorithm results. The Pie charts tab shows stored agent-level averages and aggregate measures. Neither view recalculates study results.</p>`}
function selectAverage(dataset,metric){const a=DATA.agents.find(x=>x.dataset===dataset)||{};const m=AVG_METRICS.find(x=>x.key===metric);if(!m)return;selectedKey=`avg:${dataset}|${metric}`;renderHeat();renderPies();$('#compareDetail').innerHTML=`<h2>${esc(dataset)}</h2><p class="muted">Overall agent summary</p><div class="sec"><h3>${esc(m.label)}</h3><div class="kvgrid">${kv('Selected overall value',pct(a[metric]))}${kv('Mean semantic behavioural',pct(a.meanBehavioural))}${kv('Common Test accuracy',pct(a.commonTestAccuracy))}${kv('Combined Behavioural Measure',pct(a.combinedBehavioural))}${kv('Semantic Boundary Variance',pct(a.boundaryVariance))}${kv('Mean Automated Rubric',pct(a.meanAutomatedRubric))}${kv('Mean Human Rubric',pct(a.meanHumanRubric))}${kv('Mean Human/Auto Agreement',pct(a.meanHumanAgreement))}${kv('Mean Combined Rubric',pct(a.meanCombinedRubric))}${kv('Human reviews completed',`${a.humanReviewsCompleted??0} / 50`)}</div></div><p class="detail-note">These are the stored overall agent metrics used by the comparative summary and ranking. No per-algorithm percentile is represented by these pies.</p>`}

function showView(view){const heat=view==='heat';$('#heatView').hidden=!heat;$('#pieView').hidden=heat;$('#heatTab').setAttribute('aria-selected',String(heat));$('#pieTab').setAttribute('aria-selected',String(!heat))}
$('#heatTab').addEventListener('click',()=>showView('heat'));$('#pieTab').addEventListener('click',()=>showView('pie'));$('#clearSelection').addEventListener('click',()=>{selectedKey=null;renderHeat();renderPies();$('#compareDetail').innerHTML='<h2>Comparative inspection</h2><p class="muted">Select a heat-map cell for an algorithm result, or an overall pie for an agent-level metric.</p>'});renderHeat();renderPies();renderRank();
</script></body></html>'''
    return template.replace("__COMMON_CSS__", _COMMON_CSS).replace("__DATA__", j)


def _dashboard_template(name: str) -> str:
    """Read one bundled presentation template shipped with the study build."""
    path = Path(__file__).resolve().parent / "dashboard_templates" / name
    return path.read_text(encoding="utf-8")


def _reference_comparison(value: Any, score: Any = None) -> str:
    """Present historical baseline field names using the study's frozen-reference terminology."""
    raw = str(value or "").upper()
    if raw in {"AT_REFERENCE", "AT_BASELINE", "AT_FROZEN_REFERENCE"}:
        return "AT_REFERENCE"
    if raw in {"BELOW_REFERENCE", "BELOW_BASELINE", "BELOW_FROZEN_REFERENCE"}:
        return "BELOW_REFERENCE"
    if raw in {"NOT_EVALUABLE", "NOT_COMPARABLE", ""}:
        return "NOT_EVALUABLE" if _number(score) is None else raw or "NOT_EVALUABLE"
    return raw


def _reference_dashboard_data(study_root: Path) -> dict[str, Any]:
    """Build the data structures consumed by the supplied comparative dashboards.

    This only reformats already-written study artefacts. No scores, tests, review
    decisions or pipeline stages are executed here. The study-level algorithm
    denominator N is established by the first LLM dataset and reused for every
    comparative view.
    """
    study_root = Path(study_root)
    algorithm_count, algorithm_ids, consistency = _study_algorithm_design(study_root)
    records: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    model_order: list[str] = []

    for results, analysis, report, rows in _discover_completed_llm_batches(study_root):
        batch = _batch_dashboard_data(results, analysis)
        batch_algorithms = {int(item.get("algorithm") or 0): item for item in batch.get("algorithms", [])}
        model = str(report.get("dataset") or results.parent.name)
        model_order.append(model)
        agent_records: list[dict[str, Any]] = []
        for aid in algorithm_ids:
            item = batch_algorithms.get(aid, {"algorithm": aid})
            row = rows.get(aid, {})
            score = _number(item.get("score"))
            comparison = _reference_comparison(item.get("comparison"), score)
            rec = {
                "model": model,
                "algorithm": aid,
                "behaviouralScore": score,
                "delta": _number(row.get("DeltaFromBaselinePercentagePoints")),
                "comparison": comparison,
                "comparisonStatus": row.get("ComparisonStatus"),
                "pipelineStatus": item.get("pipelineStatus"),
                "pipelineSuccess": item.get("pipelineSuccess"),
                "batchAction": item.get("batchAction"),
                "sourceSufficiency": row.get("SourceSufficiency"),
                "scoreStatus": row.get("ScoreStatus"),
                "behaviouralEvidenceAdequacy": item.get("behaviouralEvidenceAdequacy"),
                "canonicalisation": item.get("canonicalisation"),
                "ast": item.get("ast"),
                "flow": item.get("flow"),
                "python": item.get("python"),
                "testAccuracy": item.get("testAccuracy"),
                "testsDeclared": row.get("G2TestsDeclared"),
                "testsEvaluable": row.get("G2TestsEvaluable"),
                "testsPassed": row.get("G2TestsPassed"),
                "testsNotEvaluable": row.get("G2TestsNotEvaluable"),
                "normalCoverage": row.get("G2NormalPathCoverage"),
                "branchCoverage": row.get("G2BranchCoverage"),
                "boundaryCoverage": row.get("G2BoundaryCoverage"),
                "errorCoverage": row.get("G2ErrorCoverage"),
                "terminationCoverage": row.get("G2TerminationCoverage"),
                "stateMutationCoverage": row.get("G2StateMutationCoverage"),
                "failureTaxonomy": item.get("failureTaxonomy"),
                "firstSemanticLossStage": item.get("firstSemanticLossStage"),
                "firstSemanticLossCriterion": item.get("firstSemanticLossCriterion"),
                "flowchartEffect": row.get("FlowchartEffect"),
                "flowchartDelta": _number(row.get("FlowchartDelta")),
                "cyclomaticComplexity": item.get("cyclomaticComplexity"),
                "decisionCount": item.get("decisionCount"),
                "loopCount": item.get("loopCount"),
                "maximumLoopNesting": item.get("maximumLoopNesting"),
                "executableASTNodes": row.get("ExecutableASTNodes"),
                "g2Summary": item.get("g2Summary"),
                "g2Strengths": item.get("g2Strengths"),
                "g2Limitations": item.get("g2Limitations"),
                "g2Interpretation": row.get("G2Interpretation"),
                "pseudocode": item.get("pseudocode"),
                "generatedPython": item.get("generatedPython"),
                "generatedPythonPath": item.get("generatedPythonPath"),
            }
            records.append(rec)
            agent_records.append(rec)

        def count_status(value: str) -> int:
            return sum(1 for r in agent_records if str(r.get("pipelineStatus") or "").upper() == value)

        at_reference = sum(1 for r in agent_records if r.get("comparison") == "AT_REFERENCE")
        below_reference = sum(1 for r in agent_records if r.get("comparison") == "BELOW_REFERENCE")
        not_evaluable = sum(1 for r in agent_records if r.get("behaviouralScore") is None)
        summaries.append({
            "model": model,
            "meanBehavioural": _number(report.get("mean_experimental_behavioural_percentage")),
            "commonTestAccuracy": _number(report.get("semantic_test_accuracy_percentage")),
            "success": count_status("SUCCESS"),
            "failure": count_status("FAILURE"),
            "expectedFailure": count_status("EXPECTED_FAILURE"),
            "atReference": at_reference,
            "belowReference": below_reference,
            "notEvaluable": not_evaluable,
        })

    study = {
        "algorithms": algorithm_count,
        "algorithmIds": algorithm_ids,
        "agents": len(model_order),
        "instances": len(records),
        "evaluable": sum(1 for r in records if r.get("behaviouralScore") is not None),
        "notEvaluable": sum(1 for r in records if r.get("behaviouralScore") is None),
        "atReference": sum(1 for r in records if r.get("comparison") == "AT_REFERENCE"),
        "belowReference": sum(1 for r in records if r.get("comparison") == "BELOW_REFERENCE"),
        "datasetConsistency": consistency,
    }
    return {"records": records, "summaries": summaries, "modelOrder": model_order, "study": study}


def _comparative_radial_data(reference_data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for s in sorted(
        reference_data.get("summaries") or [],
        key=lambda x: (-(x.get("meanBehavioural") if x.get("meanBehavioural") is not None else -1), str(x.get("model") or "").casefold()),
    ):
        rows.append({
            "model": s.get("model"),
            "algorithmCount": int((reference_data.get("study") or {}).get("algorithms") or 0),
            "meanSemanticScore": s.get("meanBehavioural"),
            "aggregateAccuracy": s.get("commonTestAccuracy"),
            "reference": {
                "At Reference": s.get("atReference") or 0,
                "Below Reference": s.get("belowReference") or 0,
                "Not Evaluable": s.get("notEvaluable") or 0,
            },
            "pipeline": {
                "Success": s.get("success") or 0,
                "Failure": s.get("failure") or 0,
                "Expected Failure": s.get("expectedFailure") or 0,
            },
        })
    return rows


def _radial_profile_data(reference_data: dict[str, Any]) -> list[dict[str, Any]]:
    by_model: dict[str, list[dict[str, Any]]] = {}
    for r in reference_data.get("records") or []:
        by_model.setdefault(str(r.get("model")), []).append(r)
    summaries = {str(s.get("model")): s for s in reference_data.get("summaries") or []}
    out = []
    for model in reference_data.get("modelOrder") or []:
        s = summaries.get(model, {})
        algorithms = []
        for r in sorted(by_model.get(model, []), key=lambda x: int(x.get("algorithm") or 0)):
            algorithms.append({
                "algorithm": r.get("algorithm"),
                "score": r.get("behaviouralScore"),
                "pipelineStatus": r.get("pipelineStatus"),
                "comparison": r.get("comparison"),
                "testsEvaluable": r.get("testsEvaluable"),
                "testsPassed": r.get("testsPassed"),
                "testsNotEvaluable": r.get("testsNotEvaluable"),
            })
        out.append({
            "name": model,
            "slug": "".join(ch.lower() if ch.isalnum() else "_" for ch in model).strip("_"),
            "algorithmCount": int((reference_data.get("study") or {}).get("algorithms") or len(algorithms)),
            "meanSemanticScore": s.get("meanBehavioural"),
            "aggregateAccuracy": s.get("commonTestAccuracy"),
            "algorithms": algorithms,
        })
    return out


def _final_scoring_data(study_root: Path, reference_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Build model-level Final Scoring data using a fixed-denominator terminal-outcome rule.

    Human Review Overall uses the study denominator N. A completed review with a
    numerical Human Rubric percentage contributes that observed percentage. A
    completed review whose adjudicated ``score_status`` is
    ``HUMAN_REVIEW_COMPLETE_NOT_EVALUABLE`` is a terminal non-scorable outcome and
    contributes 0% under the explicitly reported failure-to-demonstrate rule.
    Incomplete reviews and unexplained/technical missing scores are never converted
    to zero: they keep Human Review Overall and Combined Final withheld.

    The numerical-only mean remains available as a descriptive audit statistic so
    readers can see the effect of any zero-credit terminal outcomes.
    """
    presentation = _study_dashboard_data(study_root)
    human = {str(a.get("dataset")): a for a in presentation.get("agents") or []}
    out = []
    for s in reference_data.get("summaries") or []:
        model = str(s.get("model"))
        semantic = _number(s.get("meanBehavioural"))
        accuracy = _number(s.get("commonTestAccuracy"))
        automated = None if semantic is None or accuracy is None else round((semantic + accuracy) / 2.0, 2)
        agent = human.get(model, {})
        completed = int(agent.get("humanReviewsCompleted") or 0)
        scored = int(agent.get("humanReviewsScored") or 0)
        required = int(agent.get("humanReviewsRequired") or (reference_data.get("study") or {}).get("algorithms") or 0)
        completed_mean = _number(agent.get("meanCompletedHumanRubric"))
        non_scorable_ids = [int(x) for x in (agent.get("humanReviewsCompletedNonScorableIds") or [])]
        unresolved_ids = [int(x) for x in (agent.get("humanReviewsCompletedUnresolvedMissingScoreIds") or [])]
        unscored_completed_ids = sorted(non_scorable_ids + unresolved_ids)
        non_scorable = len(non_scorable_ids)
        unresolved = len(unresolved_ids)
        terminal_resolved = scored + non_scorable

        # A terminal non-scorable review receives explicit zero credit while
        # remaining in the fixed N denominator. No technical/incomplete record is
        # silently imputed. Because the non-scorable contribution is zero, the
        # numerator is simply the sum of the observed numerical percentages.
        zero_adjusted_human = None
        if required > 0 and completed == required and terminal_resolved == required and unresolved == 0:
            if scored == 0:
                zero_adjusted_human = 0.0
            elif completed_mean is not None:
                zero_adjusted_human = round((completed_mean * scored) / required, 2)

        eligible = zero_adjusted_human is not None
        if completed < required:
            eligibility = "WITHHELD_INCOMPLETE_REVIEW_COVERAGE"
        elif unresolved > 0:
            eligibility = "WITHHELD_COMPLETED_REVIEW_WITH_UNRESOLVED_MISSING_HUMAN_RUBRIC"
        elif terminal_resolved < required:
            eligibility = "WITHHELD_UNRESOLVED_HUMAN_REVIEW_OUTCOME"
        else:
            eligibility = "ELIGIBLE_COMPLETE_N_OF_N_WITH_ZERO_CREDIT_NON_SCORABLE"

        coverage = round((completed / required) * 100.0, 2) if required else 0.0
        numeric_coverage = round((scored / required) * 100.0, 2) if required else 0.0
        terminal_coverage = round((terminal_resolved / required) * 100.0, 2) if required else 0.0
        out.append({
            "model": model,
            "semanticScore": semantic,
            "accuracyScore": accuracy,
            "automatedOverall": automated,
            "humanScore": zero_adjusted_human if eligible else None,
            "humanCompletedMeanDescriptive": completed_mean,
            "humanReviewsCompleted": completed,
            "humanReviewsScored": scored,
            "humanReviewsCompletedWithoutScore": len(unscored_completed_ids),
            "humanReviewsCompletedWithoutScoreIds": unscored_completed_ids,
            "humanReviewsCompletedNonScorable": non_scorable,
            "humanReviewsCompletedNonScorableIds": non_scorable_ids,
            "humanReviewsCompletedUnresolvedMissingScore": unresolved,
            "humanReviewsCompletedUnresolvedMissingScoreIds": unresolved_ids,
            "humanReviewsTerminalResolved": terminal_resolved,
            "humanReviewsRequired": required,
            "humanReviewCoveragePercentage": coverage,
            "humanNumericScoreCoveragePercentage": numeric_coverage,
            # Compatibility field retained; now represents terminal score coverage
            # because completed non-scorable reviews are explicitly scored 0%.
            "humanScoreCoveragePercentage": terminal_coverage,
            "humanTerminalOutcomeCoveragePercentage": terminal_coverage,
            "humanScoreEligible": eligible,
            "humanScoreEligibility": eligibility,
            "humanZeroCreditRuleApplied": non_scorable > 0,
            "humanZeroCreditCount": non_scorable,
            "humanZeroCreditAlgorithmIds": non_scorable_ids,
            "success": s.get("success") or 0,
            "failure": s.get("failure") or 0,
            "expectedFailure": s.get("expectedFailure") or 0,
            "atReference": s.get("atReference") or 0,
            "belowReference": s.get("belowReference") or 0,
            "notEvaluable": s.get("notEvaluable") or 0,
        })
    out.sort(key=lambda x: (-(x.get("automatedOverall") if x.get("automatedOverall") is not None else -1), x["model"].casefold()))
    return out


def _render_reference_template(name: str, placeholder: str, value: Any, *, algorithm_count: int | None = None) -> str:
    template = _dashboard_template(name)
    if placeholder not in template:
        raise ValueError(f"Dashboard template {name!r} is missing placeholder {placeholder!r}.")
    rendered = template.replace(placeholder, _safe_json_for_script(value), 1)
    if algorithm_count is not None:
        rendered = rendered.replace("__ALGORITHM_COUNT__", str(int(algorithm_count)))
    return rendered


def generate_reference_comparative_dashboards(study_root: Path, output_directory: Path | None = None) -> dict[str, Any]:
    """Generate the canonical comparative dashboard and the approved companion layouts."""
    study_root = Path(study_root)
    output_directory = Path(output_directory) if output_directory else study_root / "analysis" / "dashboards"
    output_directory.mkdir(parents=True, exist_ok=True)
    reference_data = _reference_dashboard_data(study_root)
    algorithm_count = int((reference_data.get("study") or {}).get("algorithms") or 0)

    heat_html = _render_reference_template("interactive_heatmap_v5.html", "__DATA__", reference_data, algorithm_count=algorithm_count)

    # Stable public filename: this is the authoritative study-level comparative dashboard.
    comparative = output_directory / "NL_FDEP_comparative_dashboard.html"
    comparative.write_text(heat_html, encoding="utf-8")

    radial = output_directory / "NL-FDEP Comparative Radial Dashboard.html"
    radial.write_text(
        _render_reference_template("comparative_radial.html", "__STUDY_DATA__", _comparative_radial_data(reference_data), algorithm_count=algorithm_count),
        encoding="utf-8",
    )

    profiles = output_directory / f"NL-FDEP All AI Agents - {algorithm_count}-Algorithm Radial Profiles.html"
    profiles.write_text(
        _render_reference_template("all_agents_radial_profiles.html", "__AGENTS__", _radial_profile_data(reference_data), algorithm_count=algorithm_count),
        encoding="utf-8",
    )

    final_scoring = output_directory / "NL-FDEP Final Scoring Dashboard.html"
    final_scoring.write_text(
        _render_reference_template("final_scoring.html", "__BASE_DATA__", _final_scoring_data(study_root, reference_data), algorithm_count=algorithm_count),
        encoding="utf-8",
    )

    consistency = (reference_data.get("study") or {}).get("datasetConsistency") or {}
    return {
        "status": "GENERATED",
        "dashboard_schema_version": DASHBOARD_SCHEMA_VERSION,
        "completed_agent_count": len(reference_data.get("modelOrder") or []),
        "expected_algorithm_count": algorithm_count,
        "dataset_consistency_status": consistency.get("status"),
        "dataset_mismatch_count": consistency.get("mismatch_count"),
        "dataset_consistency_file": consistency.get("status_file"),
        "comparative_dashboard": str(comparative.resolve()),
        # Compatibility status key only: no duplicate v5 HTML artefact is generated.
        "interactive_heatmap_dashboard": str(comparative.resolve()),
        "comparative_radial_dashboard": str(radial.resolve()),
        "radial_profiles_dashboard": str(profiles.resolve()),
        "final_scoring_dashboard": str(final_scoring.resolve()),
    }

def generate_study_dashboard(study_root: Path, output_directory: Path | None = None) -> dict[str, Any]:
    """Generate the requested comparative dashboard suite from existing study artefacts."""
    return generate_reference_comparative_dashboards(study_root, output_directory)


def infer_study_root(batch_root: Path, batch_type: str | None) -> Path | None:
    batch_root = Path(batch_root)
    if str(batch_type or "").upper() == "LLM_RESULTS":
        if batch_root.name.casefold() == "results":
            return batch_root.parent.parent
        return batch_root.parent
    if str(batch_type or "").upper() == "BASELINE":
        # Baseline dashboard generation is called with Baseline/pseudocode so
        # the algorithm folders can be inspected directly.
        if batch_root.name.casefold() == "pseudocode" and batch_root.parent.name.casefold() == "baseline":
            return batch_root.parent.parent
        return batch_root.parent
    return None




def _central_batch_dashboard_directory(batch_root: Path, batch_type: str | None) -> Path | None:
    """Return the central presentation directory for one batch dashboard.

    Batch analysis evidence remains beside the batch in ``study_analysis``. HTML
    dashboards are presentation artefacts and are centralised under the study
    root so operators do not need to search every agent's results tree.
    """
    batch_root = Path(batch_root)
    study_root = infer_study_root(batch_root, batch_type)
    if study_root is None:
        return None
    kind = str(batch_type or "").upper()
    if kind == "LLM_RESULTS":
        agent_name = batch_root.parent.name if batch_root.name.casefold() == "results" else batch_root.name
    elif kind == "BASELINE":
        agent_name = "Baseline"
    else:
        agent_name = batch_root.name
    return study_root / "analysis" / "dashboards" / agent_name


def _remove_legacy_batch_dashboard(analysis_directory: Path) -> bool:
    """Best-effort removal of the active legacy dashboard directory.

    Immutable ``run_history`` snapshots are deliberately not rewritten. A
    Windows/OneDrive lock on an old presentation folder must never abort
    generation of the authoritative central dashboards.
    """
    legacy = Path(analysis_directory) / "dashboards"
    if not legacy.is_dir():
        return True
    try:
        shutil.rmtree(legacy)
        return True
    except OSError:
        return False


def _generate_all_completed_batch_dashboards(study_root: Path) -> list[str]:
    """Create/refresh central dashboards for every completed batch in a study."""
    study_root = Path(study_root)
    generated: list[str] = []
    for results, analysis, _report, _rows in _discover_completed_llm_batches(study_root):
        output = study_root / "analysis" / "dashboards" / results.parent.name
        result = generate_batch_dashboard(results, analysis, output)
        generated.append(str(result["batch_dashboard"]))
        _remove_legacy_batch_dashboard(analysis)

    baseline_root = study_root / "Baseline"
    baseline_analysis = baseline_root / "study_analysis"
    baseline_report = _read_json(baseline_analysis / "batch_report.json")
    if isinstance(baseline_report, dict) and str(baseline_report.get("batch_type") or "").upper() == "BASELINE":
        pseudo = baseline_root / "pseudocode"
        batch_root = pseudo if pseudo.is_dir() else baseline_root
        output = study_root / "analysis" / "dashboards" / "Baseline"
        result = generate_batch_dashboard(batch_root, baseline_analysis, output)
        generated.append(str(result["batch_dashboard"]))
        _remove_legacy_batch_dashboard(baseline_analysis)
    return generated


def regenerate_study_dashboards(study_root: Path) -> dict[str, Any]:
    """Rebuild all central dashboard views from already-written study artefacts.

    This is presentation-only: it never runs algorithms, scoring, tests,
    adjudication, canonicalisation, or flow generation.
    """
    study_root = Path(study_root)
    generated = _generate_all_completed_batch_dashboards(study_root)
    comparative = generate_study_dashboard(study_root)
    human_review = generate_human_review_dashboard(study_root)
    return {
        "status": "GENERATED",
        "individual_dashboards": generated,
        "comparative_dashboard": comparative.get("comparative_dashboard"),
        "interactive_heatmap_dashboard": comparative.get("interactive_heatmap_dashboard"),
        "comparative_radial_dashboard": comparative.get("comparative_radial_dashboard"),
        "radial_profiles_dashboard": comparative.get("radial_profiles_dashboard"),
        "final_scoring_dashboard": comparative.get("final_scoring_dashboard"),
        "completed_agent_count": comparative.get("completed_agent_count"),
        "expected_algorithm_count": comparative.get("expected_algorithm_count"),
        "dataset_consistency_status": comparative.get("dataset_consistency_status"),
        "dataset_mismatch_count": comparative.get("dataset_mismatch_count"),
        "dataset_consistency_file": comparative.get("dataset_consistency_file"),
        "human_review_dashboard": human_review.get("human_review_dashboard"),
        "human_review_record_count": human_review.get("review_record_count"),
        "human_reviewer_count": human_review.get("reviewer_count"),
    }


def generate_dashboards_for_completed_batch(batch_root: Path, analysis_directory: Path | None = None, batch_type: str | None = None) -> dict[str, Any]:
    """Best-effort dashboard generation after batch evidence is finalised.

    Dashboard failure is deliberately non-fatal: scoring artefacts are already
    complete and remain authoritative. A status file records any presentation
    layer failure for the operator.
    """
    batch_root = Path(batch_root)
    analysis_directory = Path(analysis_directory) if analysis_directory else batch_root / "study_analysis"
    status_path = analysis_directory / "dashboard_generation.json"
    payload: dict[str, Any] = {
        "dashboard_schema_version": DASHBOARD_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "batch_type": batch_type,
        "status": "FAILED",
        "batch_dashboard": None,
        "comparative_dashboard": None,
        "interactive_heatmap_dashboard": None,
        "comparative_radial_dashboard": None,
        "radial_profiles_dashboard": None,
        "final_scoring_dashboard": None,
        "comparative_completed_agent_count": None,
        "expected_algorithm_count": None,
        "dataset_consistency_status": None,
        "dataset_mismatch_count": None,
        "dataset_consistency_file": None,
        "human_review_dashboard": None,
        "human_review_record_count": None,
        "human_reviewer_count": None,
        "error": None,
    }
    try:
        study_root = infer_study_root(batch_root, batch_type)
        central_batch_dir = _central_batch_dashboard_directory(batch_root, batch_type)
        batch = generate_batch_dashboard(batch_root, analysis_directory, central_batch_dir)
        payload["batch_dashboard"] = batch.get("batch_dashboard")
        _remove_legacy_batch_dashboard(analysis_directory)
        if study_root is not None and study_root.is_dir():
            # Refresh every completed individual dashboard so the central
            # analysis folder is complete even when earlier batches finished
            # under the legacy per-study_analysis layout.
            _generate_all_completed_batch_dashboards(study_root)
            study = generate_study_dashboard(study_root)
            payload["comparative_dashboard"] = study.get("comparative_dashboard")
            payload["interactive_heatmap_dashboard"] = study.get("interactive_heatmap_dashboard")
            payload["comparative_radial_dashboard"] = study.get("comparative_radial_dashboard")
            payload["radial_profiles_dashboard"] = study.get("radial_profiles_dashboard")
            payload["final_scoring_dashboard"] = study.get("final_scoring_dashboard")
            payload["comparative_completed_agent_count"] = study.get("completed_agent_count")
            payload["expected_algorithm_count"] = study.get("expected_algorithm_count")
            payload["dataset_consistency_status"] = study.get("dataset_consistency_status")
            payload["dataset_mismatch_count"] = study.get("dataset_mismatch_count")
            payload["dataset_consistency_file"] = study.get("dataset_consistency_file")
            human_review = generate_human_review_dashboard(study_root)
            payload["human_review_dashboard"] = human_review.get("human_review_dashboard")
            payload["human_review_record_count"] = human_review.get("review_record_count")
            payload["human_reviewer_count"] = human_review.get("reviewer_count")
        payload["status"] = "GENERATED"
    except Exception as exc:  # Presentation-layer failure must not invalidate the study batch.
        payload["error"] = f"{type(exc).__name__}: {exc}"
    analysis_directory.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    payload["status_file"] = str(status_path.resolve())
    return payload
