"""Flatten per-algorithm scoring JSON into analysis-ready CSV/JSON tables."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import csv
import json

CRITERIA = [
    "C1", "C2", "C3", "C4",
    "A1", "A2", "A3", "A4",
    "F1", "F2", "F3", "F4",
    "P1", "P2", "P3", "P4",
]


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _criterion_map(score: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    for stage in score.get("stages", {}).values():
        for criterion in stage.get("criteria", []):
            cid = criterion.get("criterion_id")
            if cid:
                out[cid] = criterion
    return out


def _selected_score(criterion: dict[str, Any]) -> tuple[int | None, str, str]:
    """Return the automated rubric stream.

    RC6 deliberately ignores legacy criterion-level human substitution in older
    ``final_assessment`` fields. Human scores are exposed in parallel columns and
    the combined score exists only at overall-rubric level.
    """
    auto = criterion.get("automated_assessment", {}) or {}
    return auto.get("score"), str(auto.get("status")), "AUTOMATED"


def _human_score(criterion: dict[str, Any]) -> tuple[int | None, str, str]:
    human = criterion.get("human_assessment", {}) or {}
    if not human.get("completed"):
        return None, "PENDING", "HUMAN"
    label = human.get("score_label")
    score = human.get("score")
    status = human.get("status")
    if not status:
        if label == "NA":
            status = "NOT_EVALUABLE"
        elif score == 0:
            status = "FAIL"
        elif score == 1:
            status = "PARTIAL"
        elif score == 2:
            status = "PASS"
        else:
            status = "NOT_EVALUABLE"
    return score, str(status), "HUMAN"


def _rubric_flat_fields(score: dict[str, Any]) -> dict[str, Any]:
    rubric_scores = score.get("rubric_scores") or {}
    automated = rubric_scores.get("automated") or {}
    human = rubric_scores.get("human") or {}
    combined = rubric_scores.get("combined") or {}
    return {
        "AutomatedRubricPercent": automated.get("percentage"),
        "HumanRubricPercent": human.get("percentage"),
        "CombinedRubricPercent": combined.get("percentage"),
        "CombinedRubricAvailable": combined.get("available", False),
        "CombinedRubricMethod": combined.get("method"),
        "HumanCriteriaCompleted": human.get("criteria_completed", 0),
        "HumanCriteriaTotal": human.get("criteria_total"),
        "HumanRubricComplete": human.get("complete", False),
    }


def _stage_parallel_fields(stages: dict[str, Any]) -> dict[str, Any]:
    mapping = {
        "canonicalisation": "Canonicalisation",
        "ast": "AST",
        "flow_diagram": "Flow",
        "python": "Python",
    }
    out: dict[str, Any] = {}
    for key, label in mapping.items():
        stage = stages.get(key, {}) or {}
        out[f"Human{label}Percent"] = (stage.get("human_stage_summary") or {}).get("percentage")
        out[f"Combined{label}Percent"] = stage.get("combined_stage_percentage")
    return out


def _g2_flat_fields(score: dict[str, Any]) -> dict[str, Any]:
    g2 = score.get("behavioural_evidence_adequacy") or {}
    counts = g2.get("test_counts") or {}
    dims = g2.get("coverage_dimensions") or {}
    def dim(name: str) -> Any:
        value = dims.get(name) or {}
        return value.get("status") if isinstance(value, dict) else value
    return {
        "BehaviouralEvidenceAdequacy": g2.get("final_result") or g2.get("result"),
        "G2Summary": g2.get("summary"),
        "G2TestsDeclared": counts.get("declared"),
        "G2TestsEvaluable": counts.get("evaluable"),
        "G2TestsPassed": counts.get("passed"),
        "G2TestsNotEvaluable": counts.get("not_evaluable"),
        "G2NormalPathCoverage": dim("normal_path"),
        "G2BranchCoverage": dim("branch_behaviour"),
        "G2BoundaryCoverage": dim("boundary_behaviour"),
        "G2ErrorCoverage": dim("error_behaviour"),
        "G2TerminationCoverage": dim("termination_behaviour"),
        "G2StateMutationCoverage": dim("state_mutation"),
        "G2Strengths": " | ".join(str(v) for v in (g2.get("strengths") or [])),
        "G2Limitations": " | ".join(str(v) for v in (g2.get("limitations") or [])),
        "G2CoverageBasis": g2.get("coverage_basis"),
        "G2Interpretation": g2.get("interpretation"),
    }



def _semantic_boundary_flat_fields(score: dict[str, Any], batch_record: dict[str, Any] | None = None) -> dict[str, Any]:
    boundary = {}
    if score:
        boundary = ((score.get("behavioural_testing") or {}).get("semantic_boundary") or {})
        if not boundary:
            boundary = ((score.get("benchmark") or {}).get("semantic_boundary") or {})
    batch_record = batch_record or {}
    return {
        "SemanticBoundaryProbesDeclared": boundary.get("declared_probes"),
        "SemanticBoundaryProbesEvaluable": boundary.get("evaluable_probes", batch_record.get("semantic_boundary_probes_evaluable")),
        "SemanticBoundaryAccepted": boundary.get("out_of_domain_accepted", batch_record.get("semantic_boundary_probes_accepted")),
        "SemanticBoundaryControlledRejection": boundary.get("controlled_rejection", batch_record.get("semantic_boundary_probes_controlled_rejection")),
        "SemanticBoundaryIncidentalFailure": boundary.get("incidental_failure", batch_record.get("semantic_boundary_probes_incidental_failure")),
        "SemanticBoundaryNotEvaluable": boundary.get("not_evaluable", batch_record.get("semantic_boundary_probes_not_evaluable")),
        "SemanticBoundaryVariancePercent": boundary.get("variance_percentage", batch_record.get("semantic_boundary_variance_percentage")),
    }

def _unscored_batch_row(record: dict[str, Any]) -> dict[str, Any]:
    """Represent a batch-level failure/review-protected item without inventing scores."""
    row: dict[str, Any] = {
        "Dataset": record.get("dataset"),
        "Algorithm": record.get("algorithm_id"),
        "SourceSufficiency": "NOT_EVALUABLE",
        "Scored": False,
        "PipelineStatus": record.get("status"),
        "PipelineSuccess": record.get("pipeline_success"),
        "BatchAction": record.get("action"),
        "BatchError": record.get("error"),
        "CalibrationStatus": record.get("calibration_status"),
        "BaselineReferenceValidationStatus": record.get("reference_validation_status"),
        "BaselineBehaviouralAgreementPercent": record.get("behavioural_agreement_percentage"),
        "BaselineCalibrationPercent": record.get("baseline_calibration_percentage"),
        "ExperimentalBehaviouralPercent": record.get("experimental_behavioural_percentage"),
        "DeltaFromBaselinePercentagePoints": record.get("delta_from_baseline_percentage_points"),
        "ComparisonToBaseline": record.get("comparison_to_baseline"),
        "ComparisonStatus": "NOT_EVALUABLE",
        "CommonTestSet": None,
        "SemanticBoundaryProbesDeclared": None,
        "SemanticBoundaryProbesEvaluable": record.get("semantic_boundary_probes_evaluable"),
        "SemanticBoundaryAccepted": record.get("semantic_boundary_probes_accepted"),
        "SemanticBoundaryControlledRejection": record.get("semantic_boundary_probes_controlled_rejection"),
        "SemanticBoundaryIncidentalFailure": record.get("semantic_boundary_probes_incidental_failure"),
        "SemanticBoundaryNotEvaluable": record.get("semantic_boundary_probes_not_evaluable"),
        "SemanticBoundaryVariancePercent": record.get("semantic_boundary_variance_percentage"),
    }
    for cid in CRITERIA:
        row[cid] = None
        row[f"{cid}_Status"] = "NOT_EVALUABLE"
        row[f"{cid}_Source"] = "NONE"
        row[f"{cid}_Human"] = None
        row[f"{cid}_HumanStatus"] = "PENDING"
    row.update({
        "CanonicalisationPercent": None, "ASTPercent": None, "FlowPercent": None, "PythonPercent": None,
        "TestAccuracyPercent": None, "CompleteCorrectness": None,
        "FlowchartDelta": None, "FlowchartEffect": "NOT_EVALUABLE",
        "FlowMediationDelta": None, "FlowMediationEffect": "NOT_EVALUABLE",
        "DirectASTTestAccuracyPercent": None, "FlowMediatedTestAccuracyPercent": None,
        "FailureTaxonomy": None, "FirstSemanticLossStage": None, "FirstSemanticLossCriterion": None,
        "CyclomaticComplexity": None, "DecisionCount": None, "LoopCount": None,
        "MaximumLoopNesting": None, "ExecutableASTNodes": None,
        "ScoreStatus": "UNSCORED_BATCH_RESULT", "ReviewerAgreementPercent": None,
        "AutomatedRubricPercent": None, "HumanRubricPercent": None, "CombinedRubricPercent": None,
        "CombinedRubricAvailable": False, "CombinedRubricMethod": None,
        "HumanCriteriaCompleted": 0, "HumanCriteriaTotal": len(CRITERIA), "HumanRubricComplete": False,
        "HumanCanonicalisationPercent": None, "HumanASTPercent": None, "HumanFlowPercent": None, "HumanPythonPercent": None,
        "CombinedCanonicalisationPercent": None, "CombinedASTPercent": None, "CombinedFlowPercent": None, "CombinedPythonPercent": None,
        "BehaviouralEvidenceAdequacy": "NOT_EVALUABLE", "G2Summary": "No completed scoring artefact is available for behavioural evidence assessment.",
        "G2TestsDeclared": None, "G2TestsEvaluable": None, "G2TestsPassed": None, "G2TestsNotEvaluable": None,
        "G2NormalPathCoverage": "NOT_EVALUABLE", "G2BranchCoverage": "NOT_EVALUABLE", "G2BoundaryCoverage": "NOT_EVALUABLE",
        "G2ErrorCoverage": "NOT_EVALUABLE", "G2TerminationCoverage": "NOT_EVALUABLE", "G2StateMutationCoverage": "NOT_EVALUABLE",
        "G2Strengths": "", "G2Limitations": "No completed scoring artefact is available.",
        "G2CoverageBasis": "Batch-level failure/review-protected item.", "G2Interpretation": "Behavioural evidence adequacy is not evaluable for this row.",
    })
    return row


def aggregate_algorithm_folders(parent: Path, analysis_directory: Path | None = None) -> dict[str, str]:
    parent = Path(parent)
    analysis_directory = Path(analysis_directory) if analysis_directory else parent / "study_analysis"
    analysis_directory.mkdir(parents=True, exist_ok=True)

    score_files = sorted(parent.glob("Algorithm - */pipeline_artifacts/scoring/final_score.json"))
    batch_report = _read_json(analysis_directory / "batch_report.json") or {}
    batch_records = {
        (record.get("dataset"), record.get("algorithm_id")): record
        for record in batch_report.get("algorithms", []) if isinstance(record, dict)
    }
    preflight = _read_json(analysis_directory / "study_preflight.json") or {}
    dataset_name = batch_report.get("dataset")
    for row in preflight.get("algorithms", []):
        if not isinstance(row, dict):
            continue
        issues=set(row.get("issues") or [])
        missing_folder = "ALGORITHM_FOLDER_MISSING" in issues or "PSEUDOCODE_FOLDER_MISSING" in issues
        if not missing_folder:
            continue
        key=(dataset_name,row.get("algorithm_id"))
        batch_records.setdefault(key,{
            "dataset":dataset_name,"algorithm_id":row.get("algorithm_id"),"status":"NOT_RUN","pipeline_success":False,
            "action":"PREFLIGHT_FAILURE","error":";".join(sorted(issues)),"calibration_status":"PIPELINE_NOT_RUN" if str(dataset_name).casefold()=="baseline" else None,
            "reference_validation_status":None,"behavioural_agreement_percentage":None,
        })
    rows: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []
    flow_rows: list[dict[str, Any]] = []
    review_status_rows: list[dict[str, Any]] = []

    for score_path in score_files:
        score = _read_json(score_path)
        if not score:
            continue
        algorithm = score.get("algorithm", {})
        dataset = algorithm.get("dataset")
        algorithm_id = algorithm.get("algorithm_id")
        criteria = _criterion_map(score)
        source_gate = score.get("source_sufficiency", {}) or {}
        row: dict[str, Any] = {
            "Dataset": dataset,
            "Algorithm": algorithm_id,
            "SourceSufficiency": source_gate.get("result"),
            "SourceSufficiencyHuman": (source_gate.get("human_assessment") or {}).get("result"),
        }
        for cid in CRITERIA:
            c = criteria.get(cid, {})
            selected, status, source = _selected_score(c) if c else (None, "NOT_EVALUABLE", "NONE")
            human_selected, human_status, _ = _human_score(c) if c else (None, "PENDING", "HUMAN")
            row[cid] = selected
            row[f"{cid}_Status"] = status
            row[f"{cid}_Source"] = source
            row[f"{cid}_Human"] = human_selected
            row[f"{cid}_HumanStatus"] = human_status
        stages = score.get("stages", {})
        row.update({
            "CanonicalisationPercent": (stages.get("canonicalisation", {}).get("stage_summary") or {}).get("percentage"),
            "ASTPercent": (stages.get("ast", {}).get("stage_summary") or {}).get("percentage"),
            "FlowPercent": (stages.get("flow_diagram", {}).get("stage_summary") or {}).get("percentage"),
            "PythonPercent": (stages.get("python", {}).get("stage_summary") or {}).get("percentage"),
            "TestAccuracyPercent": (score.get("behavioural_testing") or {}).get("accuracy_percentage"),
            "CompleteCorrectness": (score.get("behavioural_testing") or {}).get("complete_correctness"),
            "NormalTestAccuracyPercent": (((score.get("behavioural_testing") or {}).get("category_metrics") or {}).get("NORMAL") or {}).get("accuracy_percentage"),
            "BranchTestAccuracyPercent": (((score.get("behavioural_testing") or {}).get("category_metrics") or {}).get("BRANCH") or {}).get("accuracy_percentage"),
            "BoundaryTestAccuracyPercent": (((score.get("behavioural_testing") or {}).get("category_metrics") or {}).get("BOUNDARY") or {}).get("accuracy_percentage"),
            "ErrorBehaviourTestAccuracyPercent": (((score.get("behavioural_testing") or {}).get("category_metrics") or {}).get("ERROR_BEHAVIOUR") or {}).get("accuracy_percentage"),
            "TerminationTestAccuracyPercent": (((score.get("behavioural_testing") or {}).get("category_metrics") or {}).get("TERMINATION") or {}).get("accuracy_percentage"),
            "StateMutationTestAccuracyPercent": (((score.get("behavioural_testing") or {}).get("category_metrics") or {}).get("STATE_MUTATION") or {}).get("accuracy_percentage"),
            "FlowchartDelta": (score.get("derived_metrics") or {}).get("flowchart_delta"),
            "FlowchartEffect": (score.get("derived_metrics") or {}).get("flowchart_effect"),
            "FlowMediationDelta": (score.get("derived_metrics") or {}).get("flow_mediation_delta"),
            "FlowMediationEffect": (score.get("derived_metrics") or {}).get("flow_mediation_effect"),
            "DirectASTTestAccuracyPercent": (score.get("derived_metrics") or {}).get("direct_ast_test_accuracy_percentage"),
            "FlowMediatedTestAccuracyPercent": (score.get("derived_metrics") or {}).get("flow_mediated_test_accuracy_percentage"),
            "FailureTaxonomy": (score.get("derived_metrics") or {}).get("failure_taxonomy"),
            "FirstSemanticLossStage": ((score.get("derived_metrics") or {}).get("first_semantic_loss") or {}).get("stage"),
            "FirstSemanticLossCriterion": ((score.get("derived_metrics") or {}).get("first_semantic_loss") or {}).get("criterion"),
            "CyclomaticComplexity": (score.get("complexity") or {}).get("cyclomatic_complexity"),
            "DecisionCount": (score.get("complexity") or {}).get("decision_count"),
            "LoopCount": (score.get("complexity") or {}).get("loop_count"),
            "MaximumLoopNesting": (score.get("complexity") or {}).get("maximum_loop_nesting"),
            "ExecutableASTNodes": (score.get("complexity") or {}).get("ast_executable_nodes"),
            "ScoreStatus": score.get("score_status"),
            "ReviewerAgreementPercent": (score.get("derived_metrics") or {}).get("automated_human_agreement_percentage"),
        })
        row.update(_g2_flat_fields(score))
        row["BehaviouralEvidenceAdequacyHuman"] = ((score.get("behavioural_evidence_adequacy") or {}).get("human_assessment") or {}).get("result")
        row.update(_rubric_flat_fields(score))
        row.update(_stage_parallel_fields(stages))
        benchmark = score.get("benchmark") or {}
        batch_record = batch_records.get((dataset, algorithm_id), {})
        row.update(_semantic_boundary_flat_fields(score, batch_record))
        row["BaselineBehaviouralAgreementPercent"] = benchmark.get("behavioural_agreement_percentage")
        baseline_calibration_value = (
            benchmark.get("calibration_score_percentage")
            if benchmark.get("is_baseline")
            else benchmark.get("baseline_calibration_score_percentage")
        )
        row["BaselineCalibrationPercent"] = baseline_calibration_value if baseline_calibration_value is not None else batch_record.get("baseline_calibration_percentage")
        experimental_value = (
            benchmark.get("experimental_behavioural_score_percentage")
            if not benchmark.get("is_baseline")
            else None
        )
        row["ExperimentalBehaviouralPercent"] = experimental_value if experimental_value is not None else batch_record.get("experimental_behavioural_percentage")
        row["DeltaFromBaselinePercentagePoints"] = benchmark.get("delta_from_baseline_percentage_points")
        if row["DeltaFromBaselinePercentagePoints"] is None:
            row["DeltaFromBaselinePercentagePoints"] = batch_record.get("delta_from_baseline_percentage_points")
        row["ComparisonToBaseline"] = benchmark.get("comparison_to_baseline") or batch_record.get("comparison_to_baseline")
        row["ComparisonStatus"] = benchmark.get("comparison_status") or ("CALIBRATION" if benchmark.get("is_baseline") else "NOT_EVALUABLE")
        row["CommonTestSet"] = benchmark.get("common_test_set")
        row["BaselineReferenceValidationStatus"] = (benchmark.get("reference_validation") or benchmark.get("baseline_reference_validation") or {}).get("status") or batch_record.get("reference_validation_status")
        row["CalibrationStatus"] = batch_record.get("calibration_status")
        row["Scored"] = True
        row["PipelineStatus"] = batch_record.get("status")
        row["PipelineSuccess"] = batch_record.get("pipeline_success")
        row["BatchAction"] = batch_record.get("action")
        row["BatchError"] = batch_record.get("error")
        rows.append(row)

        for cid, c in criteria.items():
            auto = c.get("automated_assessment", {})
            selected, final_status, final_source = _selected_score(c)
            human_selected, human_status, _ = _human_score(c)
            human_assessment = c.get("human_assessment", {}) or {}
            evidence_rows.append({
                "Dataset": dataset,
                "Algorithm": algorithm_id,
                "Criterion": cid,
                "Question": c.get("question"),
                "AutomatedScore": auto.get("score"),
                "AutomatedStatus": auto.get("status"),
                "AutomatedConfidence": auto.get("confidence"),
                "AutomatedJustification": auto.get("justification"),
                "HumanScore": human_selected,
                "HumanStatus": human_status,
                "HumanAgreement": human_assessment.get("agreement_with_automated_score"),
                "HumanJustification": human_assessment.get("reviewer_justification"),
                "FinalScore": selected,
                "FinalStatus": final_status,
                "FinalSource": final_source,
                "EvidenceJSON": json.dumps(c.get("evidence", []), ensure_ascii=False),
            })
            if auto.get("status") == "REVIEW_REQUIRED" or auto.get("confidence") == "LOW":
                review_rows.append({
                    "Dataset": dataset,
                    "Algorithm": algorithm_id,
                    "Criterion": cid,
                    "Question": c.get("question"),
                    "AutomatedScore": auto.get("score"),
                    "Reason": auto.get("justification"),
                })

        flow_rows.append({
            "Dataset": dataset,
            "Algorithm": algorithm_id,
            "PreFlowStagePercent": (score.get("derived_metrics") or {}).get("pre_flow_stage_percentage"),
            "PostFlowStagePercent": (score.get("derived_metrics") or {}).get("post_flow_stage_percentage"),
            "FlowchartDelta": (score.get("derived_metrics") or {}).get("flowchart_delta"),
            "FlowchartEffect": (score.get("derived_metrics") or {}).get("flowchart_effect"),
            "FlowMediationDelta": (score.get("derived_metrics") or {}).get("flow_mediation_delta"),
            "FlowMediationEffect": (score.get("derived_metrics") or {}).get("flow_mediation_effect"),
            "DirectASTTestAccuracyPercent": (score.get("derived_metrics") or {}).get("direct_ast_test_accuracy_percentage"),
            "FlowMediatedTestAccuracyPercent": (score.get("derived_metrics") or {}).get("flow_mediated_test_accuracy_percentage"),
        })
        scoring_dir = score_path.parent
        review_status_rows.append({
            "Dataset": dataset,
            "Algorithm": algorithm_id,
            "QuestionnaireGenerated": (scoring_dir / "human_review_questionnaire.html").exists(),
            "HumanReviewPresent": (scoring_dir / "human_review.json").exists(),
            "FinalScoreStatus": score.get("score_status"),
            "HumanCriteriaCompleted": (_rubric_flat_fields(score)).get("HumanCriteriaCompleted"),
            "HumanRubricComplete": (_rubric_flat_fields(score)).get("HumanRubricComplete"),
            "AutomatedRubricPercent": (_rubric_flat_fields(score)).get("AutomatedRubricPercent"),
            "HumanRubricPercent": (_rubric_flat_fields(score)).get("HumanRubricPercent"),
            "CombinedRubricPercent": (_rubric_flat_fields(score)).get("CombinedRubricPercent"),
        })

    represented={(row.get("Dataset"),row.get("Algorithm")) for row in rows}
    for key,record in batch_records.items():
        if key in represented:
            continue
        rows.append(_unscored_batch_row(record))
        review_status_rows.append({
            "Dataset": record.get("dataset"),
            "Algorithm": record.get("algorithm_id"),
            "QuestionnaireGenerated": False,
            "HumanReviewPresent": False,
            "FinalScoreStatus": "UNSCORED_BATCH_RESULT",
            "PipelineStatus": record.get("status"),
            "BatchAction": record.get("action"),
        })
    rows.sort(key=lambda row:(str(row.get("Dataset") or "").casefold(), int(row.get("Algorithm") or 0)))

    outputs = {}
    outputs["algorithm_scores_csv"] = str(_write_csv(analysis_directory / "algorithm_scores.csv", rows))
    outputs["criterion_evidence_csv"] = str(_write_csv(analysis_directory / "criterion_evidence.csv", evidence_rows))
    outputs["review_queue_csv"] = str(_write_csv(analysis_directory / "review_queue.csv", review_rows))
    outputs["flowchart_impact_csv"] = str(_write_csv(analysis_directory / "flowchart_impact.csv", flow_rows))
    outputs["human_review_status_csv"] = str(_write_csv(analysis_directory / "human_review_status.csv", review_status_rows))
    comparison_rows=[{
        "Dataset":row.get("Dataset"),"Algorithm":row.get("Algorithm"),
        "BaselineCalibrationPercent":row.get("BaselineCalibrationPercent"),
        "ExperimentalBehaviouralPercent":row.get("ExperimentalBehaviouralPercent"),
        "DeltaFromBaselinePercentagePoints":row.get("DeltaFromBaselinePercentagePoints"),
        "ComparisonToBaseline":row.get("ComparisonToBaseline"),
        "ComparisonStatus":row.get("ComparisonStatus"),
        "SemanticBoundaryVariancePercent":row.get("SemanticBoundaryVariancePercent"),
        "SemanticBoundaryProbesEvaluable":row.get("SemanticBoundaryProbesEvaluable"),
        "SemanticBoundaryAccepted":row.get("SemanticBoundaryAccepted"),
        "CommonTestSet":row.get("CommonTestSet"),
    } for row in rows]
    outputs["baseline_comparison_csv"] = str(_write_csv(analysis_directory / "baseline_comparison.csv", comparison_rows))
    json_path = analysis_directory / "algorithm_scores.json"
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    outputs["algorithm_scores_json"] = str(json_path.resolve())
    return outputs


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        if fieldnames:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    return path.resolve()


def aggregate_study_root(study_root: Path, analysis_directory: Path | None = None) -> dict[str, str]:
    """Aggregate baseline plus all ``*/results`` datasets under one study root."""
    study_root = Path(study_root)
    analysis_directory = Path(analysis_directory) if analysis_directory else study_root / "analysis"
    analysis_directory.mkdir(parents=True, exist_ok=True)

    score_files = []
    baseline_scores = study_root.glob("Baseline/pseudocode/Algorithm - */pipeline_artifacts/scoring/final_score.json")
    score_files.extend(baseline_scores)
    for results_dir in study_root.glob("*/results"):
        score_files.extend(results_dir.glob("Algorithm - */pipeline_artifacts/scoring/final_score.json"))
    score_files = sorted(set(score_files), key=lambda p: str(p).casefold())
    batch_records: dict[tuple[Any, Any], dict[str, Any]] = {}
    batch_paths = [study_root / "Baseline" / "study_analysis" / "batch_report.json"]
    batch_paths.extend(results_dir / "study_analysis" / "batch_report.json" for results_dir in study_root.glob("*/results"))
    for batch_path in batch_paths:
        batch = _read_json(batch_path) or {}
        for record in batch.get("algorithms", []):
            if isinstance(record, dict):
                batch_records[(record.get("dataset"), record.get("algorithm_id"))] = record
    unscored_analysis_rows: dict[tuple[Any, Any], dict[str, Any]] = {}
    analysis_score_paths=[study_root / "Baseline" / "study_analysis" / "algorithm_scores.json"]
    analysis_score_paths.extend(results_dir / "study_analysis" / "algorithm_scores.json" for results_dir in study_root.glob("*/results"))
    for score_table_path in analysis_score_paths:
        try:
            table=json.loads(score_table_path.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError):
            continue
        if not isinstance(table,list):
            continue
        for row in table:
            if isinstance(row,dict) and row.get("Scored") is False:
                unscored_analysis_rows[(row.get("Dataset"),row.get("Algorithm"))]=row

    # Reuse the same flattening logic by reading each score directly.
    rows=[]; evidence_rows=[]; review_rows=[]; flow_rows=[]; review_status_rows=[]
    for score_path in score_files:
        score=_read_json(score_path)
        if not score: continue
        algorithm=score.get("algorithm",{}); dataset=algorithm.get("dataset"); algorithm_id=algorithm.get("algorithm_id")
        criteria=_criterion_map(score)
        source_gate=score.get("source_sufficiency",{}) or {}
        row={"Dataset":dataset,"Algorithm":algorithm_id,"SourceSufficiency":source_gate.get("result"),"SourceSufficiencyHuman":(source_gate.get("human_assessment") or {}).get("result")}
        for cid in CRITERIA:
            c=criteria.get(cid,{})
            selected,status,source=_selected_score(c) if c else (None,"NOT_EVALUABLE","NONE")
            human_selected,human_status,_=_human_score(c) if c else (None,"PENDING","HUMAN")
            row[cid]=selected; row[f"{cid}_Status"]=status; row[f"{cid}_Source"]=source
            row[f"{cid}_Human"]=human_selected; row[f"{cid}_HumanStatus"]=human_status
        stages=score.get("stages",{}); derived=score.get("derived_metrics") or {}; beh=score.get("behavioural_testing") or {}; comp=score.get("complexity") or {}; benchmark=score.get("benchmark") or {}
        row.update({
            "CanonicalisationPercent":(stages.get("canonicalisation",{}).get("stage_summary") or {}).get("percentage"),
            "ASTPercent":(stages.get("ast",{}).get("stage_summary") or {}).get("percentage"),
            "FlowPercent":(stages.get("flow_diagram",{}).get("stage_summary") or {}).get("percentage"),
            "PythonPercent":(stages.get("python",{}).get("stage_summary") or {}).get("percentage"),
            "TestAccuracyPercent":beh.get("accuracy_percentage"),"CompleteCorrectness":beh.get("complete_correctness"),
            "NormalTestAccuracyPercent":((beh.get("category_metrics") or {}).get("NORMAL") or {}).get("accuracy_percentage"),
            "BranchTestAccuracyPercent":((beh.get("category_metrics") or {}).get("BRANCH") or {}).get("accuracy_percentage"),
            "BoundaryTestAccuracyPercent":((beh.get("category_metrics") or {}).get("BOUNDARY") or {}).get("accuracy_percentage"),
            "ErrorBehaviourTestAccuracyPercent":((beh.get("category_metrics") or {}).get("ERROR_BEHAVIOUR") or {}).get("accuracy_percentage"),
            "TerminationTestAccuracyPercent":((beh.get("category_metrics") or {}).get("TERMINATION") or {}).get("accuracy_percentage"),
            "StateMutationTestAccuracyPercent":((beh.get("category_metrics") or {}).get("STATE_MUTATION") or {}).get("accuracy_percentage"),
            "FlowchartDelta":derived.get("flowchart_delta"),"FlowchartEffect":derived.get("flowchart_effect"),
            "FlowMediationDelta":derived.get("flow_mediation_delta"),"FlowMediationEffect":derived.get("flow_mediation_effect"),
            "DirectASTTestAccuracyPercent":derived.get("direct_ast_test_accuracy_percentage"),"FlowMediatedTestAccuracyPercent":derived.get("flow_mediated_test_accuracy_percentage"),
            "FailureTaxonomy":derived.get("failure_taxonomy"),"FirstSemanticLossStage":(derived.get("first_semantic_loss") or {}).get("stage"),
            "FirstSemanticLossCriterion":(derived.get("first_semantic_loss") or {}).get("criterion"),
            "CyclomaticComplexity":comp.get("cyclomatic_complexity"),"DecisionCount":comp.get("decision_count"),"LoopCount":comp.get("loop_count"),
            "MaximumLoopNesting":comp.get("maximum_loop_nesting"),"ExecutableASTNodes":comp.get("ast_executable_nodes"),
            "ScoreStatus":score.get("score_status"),"ReviewerAgreementPercent":derived.get("automated_human_agreement_percentage"),
            "BaselineBehaviouralAgreementPercent":benchmark.get("behavioural_agreement_percentage"),
            "BaselineCalibrationPercent":benchmark.get("calibration_score_percentage") if benchmark.get("is_baseline") else benchmark.get("baseline_calibration_score_percentage"),
            "ExperimentalBehaviouralPercent":None if benchmark.get("is_baseline") else benchmark.get("experimental_behavioural_score_percentage"),
            "DeltaFromBaselinePercentagePoints":benchmark.get("delta_from_baseline_percentage_points"),
            "ComparisonToBaseline":benchmark.get("comparison_to_baseline"),
            "ComparisonStatus":benchmark.get("comparison_status") or ("CALIBRATION" if benchmark.get("is_baseline") else "NOT_EVALUABLE"),
            "CommonTestSet":benchmark.get("common_test_set"),
            "BaselineReferenceValidationStatus":(benchmark.get("reference_validation") or benchmark.get("baseline_reference_validation") or {}).get("status"),
            "BaselineReferenceValidationPercent":(benchmark.get("reference_validation") or benchmark.get("baseline_reference_validation") or {}).get("validation_percentage"),
        })
        row.update(_g2_flat_fields(score))
        row["BehaviouralEvidenceAdequacyHuman"]=((score.get("behavioural_evidence_adequacy") or {}).get("human_assessment") or {}).get("result")
        row.update(_rubric_flat_fields(score)); row.update(_stage_parallel_fields(stages))
        batch_record=batch_records.get((dataset,algorithm_id),{})
        row.update(_semantic_boundary_flat_fields(score, batch_record))
        row.update({"Scored":True,"PipelineStatus":batch_record.get("status"),"PipelineSuccess":batch_record.get("pipeline_success"),"BatchAction":batch_record.get("action"),"BatchError":batch_record.get("error"),"CalibrationStatus":batch_record.get("calibration_status")})
        if row.get("BaselineCalibrationPercent") is None: row["BaselineCalibrationPercent"]=batch_record.get("baseline_calibration_percentage")
        if row.get("ExperimentalBehaviouralPercent") is None: row["ExperimentalBehaviouralPercent"]=batch_record.get("experimental_behavioural_percentage")
        if row.get("DeltaFromBaselinePercentagePoints") is None: row["DeltaFromBaselinePercentagePoints"]=batch_record.get("delta_from_baseline_percentage_points")
        if row.get("ComparisonToBaseline") is None: row["ComparisonToBaseline"]=batch_record.get("comparison_to_baseline")
        if row.get("BaselineReferenceValidationStatus") is None: row["BaselineReferenceValidationStatus"]=batch_record.get("reference_validation_status")
        rows.append(row)
        for cid,c in criteria.items():
            auto=c.get("automated_assessment",{}); selected,final_status,final_source=_selected_score(c); human_selected,human_status,_=_human_score(c); human_assessment=c.get("human_assessment",{}) or {}
            evidence_rows.append({"Dataset":dataset,"Algorithm":algorithm_id,"Criterion":cid,"Question":c.get("question"),"AutomatedScore":auto.get("score"),"AutomatedStatus":auto.get("status"),"AutomatedConfidence":auto.get("confidence"),"AutomatedJustification":auto.get("justification"),"HumanScore":human_selected,"HumanStatus":human_status,"HumanAgreement":human_assessment.get("agreement_with_automated_score"),"HumanJustification":human_assessment.get("reviewer_justification"),"FinalScore":selected,"FinalStatus":final_status,"FinalSource":final_source,"EvidenceJSON":json.dumps(c.get("evidence",[]),ensure_ascii=False)})
            if auto.get("status")=="REVIEW_REQUIRED" or auto.get("confidence")=="LOW":
                review_rows.append({"Dataset":dataset,"Algorithm":algorithm_id,"Criterion":cid,"Question":c.get("question"),"AutomatedScore":auto.get("score"),"Reason":auto.get("justification")})
        flow_rows.append({"Dataset":dataset,"Algorithm":algorithm_id,"PreFlowStagePercent":derived.get("pre_flow_stage_percentage"),"PostFlowStagePercent":derived.get("post_flow_stage_percentage"),"FlowchartDelta":derived.get("flowchart_delta"),"FlowchartEffect":derived.get("flowchart_effect"),"DirectASTTestAccuracyPercent":derived.get("direct_ast_test_accuracy_percentage"),"FlowMediatedTestAccuracyPercent":derived.get("flow_mediated_test_accuracy_percentage"),"FlowMediationDelta":derived.get("flow_mediation_delta"),"FlowMediationEffect":derived.get("flow_mediation_effect")})
        scoring_dir=score_path.parent
        rubric_flat=_rubric_flat_fields(score)
        review_status_rows.append({"Dataset":dataset,"Algorithm":algorithm_id,"QuestionnaireGenerated":(scoring_dir/"human_review_questionnaire.html").exists(),"HumanReviewPresent":(scoring_dir/"human_review.json").exists(),"FinalScoreStatus":score.get("score_status"),"HumanCriteriaCompleted":rubric_flat.get("HumanCriteriaCompleted"),"HumanRubricComplete":rubric_flat.get("HumanRubricComplete"),"AutomatedRubricPercent":rubric_flat.get("AutomatedRubricPercent"),"HumanRubricPercent":rubric_flat.get("HumanRubricPercent"),"CombinedRubricPercent":rubric_flat.get("CombinedRubricPercent")})

    represented={(row.get("Dataset"),row.get("Algorithm")) for row in rows}
    for key,record in batch_records.items():
        if key not in represented:
            rows.append(unscored_analysis_rows.get(key) or _unscored_batch_row(record))
            review_status_rows.append({"Dataset":record.get("dataset"),"Algorithm":record.get("algorithm_id"),"QuestionnaireGenerated":False,"HumanReviewPresent":False,"FinalScoreStatus":"UNSCORED_BATCH_RESULT","PipelineStatus":record.get("status"),"BatchAction":record.get("action")})
    for key,row in unscored_analysis_rows.items():
        if key not in represented and key not in batch_records:
            rows.append(row)
    rows.sort(key=lambda row:(str(row.get("Dataset") or "").casefold(), int(row.get("Algorithm") or 0)))

    outputs={}
    outputs["all_models_scores_csv"]=str(_write_csv(analysis_directory/"all_models_scores.csv",rows))
    outputs["criterion_evidence_csv"]=str(_write_csv(analysis_directory/"criterion_evidence.csv",evidence_rows))
    outputs["review_queue_csv"]=str(_write_csv(analysis_directory/"review_queue.csv",review_rows))
    outputs["flowchart_impact_csv"]=str(_write_csv(analysis_directory/"flowchart_impact.csv",flow_rows))
    outputs["human_review_status_csv"]=str(_write_csv(analysis_directory/"human_review_status.csv",review_status_rows))
    comparison_rows=[{
        "Dataset":row.get("Dataset"),"Algorithm":row.get("Algorithm"),
        "BaselineCalibrationPercent":row.get("BaselineCalibrationPercent"),
        "ExperimentalBehaviouralPercent":row.get("ExperimentalBehaviouralPercent"),
        "DeltaFromBaselinePercentagePoints":row.get("DeltaFromBaselinePercentagePoints"),
        "ComparisonToBaseline":row.get("ComparisonToBaseline"),
        "ComparisonStatus":row.get("ComparisonStatus"),
        "SemanticBoundaryVariancePercent":row.get("SemanticBoundaryVariancePercent"),
        "SemanticBoundaryProbesEvaluable":row.get("SemanticBoundaryProbesEvaluable"),
        "SemanticBoundaryAccepted":row.get("SemanticBoundaryAccepted"),
        "CommonTestSet":row.get("CommonTestSet"),
    } for row in rows]
    outputs["baseline_comparison_csv"]=str(_write_csv(analysis_directory/"baseline_comparison.csv",comparison_rows))

    # Dataset-level means, ignoring unavailable values.
    numeric_fields=["CanonicalisationPercent","ASTPercent","FlowPercent","PythonPercent","TestAccuracyPercent","AutomatedRubricPercent","HumanRubricPercent","CombinedRubricPercent","BaselineCalibrationPercent","ExperimentalBehaviouralPercent","SemanticBoundaryVariancePercent","DeltaFromBaselinePercentagePoints","FlowchartDelta","FlowMediationDelta","CyclomaticComplexity"]
    by_dataset={}
    for row in rows: by_dataset.setdefault(row.get("Dataset"),[]).append(row)
    model_summary=[]
    for dataset,items in sorted(by_dataset.items(), key=lambda kv:str(kv[0]).casefold()):
        summary={"Dataset":dataset,"Algorithms":len(items),"ScoredAlgorithms":sum(r.get("Scored") is True for r in items),"UnscoredAlgorithms":sum(r.get("Scored") is not True for r in items)}
        for field in numeric_fields:
            vals=[float(r[field]) for r in items if r.get(field) is not None]
            summary[f"Mean{field}"]=round(sum(vals)/len(vals),2) if vals else None
            summary[f"Evaluable{field}Count"]=len(vals)
        summary["CompleteCorrectCount"]=sum(r.get("CompleteCorrectness") is True for r in items)
        model_summary.append(summary)
    outputs["model_summary_csv"]=str(_write_csv(analysis_directory/"model_summary.csv",model_summary))

    # Task difficulty across non-baseline model datasets.
    by_algorithm={}
    for row in rows:
        if str(row.get("Dataset")).casefold()=="baseline": continue
        by_algorithm.setdefault(row.get("Algorithm"),[]).append(row)
    difficulty=[]
    for aid,items in sorted(by_algorithm.items(), key=lambda kv:(kv[0] is None,kv[0])):
        test_vals=[float(r["TestAccuracyPercent"]) for r in items if r.get("TestAccuracyPercent") is not None]
        py_vals=[float(r["PythonPercent"]) for r in items if r.get("PythonPercent") is not None]
        difficulty.append({"Algorithm":aid,"ModelCount":len(items),"MeanTestAccuracyPercent":round(sum(test_vals)/len(test_vals),2) if test_vals else None,"MeanPythonPercent":round(sum(py_vals)/len(py_vals),2) if py_vals else None})
    outputs["algorithm_difficulty_csv"]=str(_write_csv(analysis_directory/"algorithm_difficulty.csv",difficulty))

    json_path=analysis_directory/"all_models_scores.json"; json_path.write_text(json.dumps(rows,indent=2),encoding="utf-8"); outputs["all_models_scores_json"]=str(json_path.resolve())
    return outputs
