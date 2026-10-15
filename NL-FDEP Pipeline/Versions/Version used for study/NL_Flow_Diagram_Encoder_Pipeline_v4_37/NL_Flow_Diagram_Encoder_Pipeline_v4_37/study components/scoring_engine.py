"""Deterministic, evidence-based scoring for NL-FDEP study artefacts."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

from semantic_signature import (
    EXECUTABLE_KINDS,
    compare_signatures,
    complexity_from_structured_program,
    flow_graph_validation,
    signature_from_ast_adjacency,
    signature_from_structured_program,
)
from study_rubric import (
    LANGUAGE_VERSION,
    PIPELINE_VERSION,
    RUBRIC_VERSION,
    SCALE,
    SCORING_SCHEMA_VERSION,
    SOURCE_GATE,
    BEHAVIOURAL_EVIDENCE_GATE,
    STAGES,
)

ACCEPTED_TRANSFORMATION_CONFIDENCE = {
    "source_proven",
    "structurally_certain",
    "user_confirmed",
}


_G2_DIMENSIONS = {
    "normal_path": ("Normal-path coverage", "NORMAL"),
    "branch_behaviour": ("Branch coverage", "BRANCH"),
    "boundary_behaviour": ("Boundary coverage", "BOUNDARY"),
    "error_behaviour": ("Error-behaviour coverage", "ERROR_BEHAVIOUR"),
    "termination_behaviour": ("Termination coverage", "TERMINATION"),
    "state_mutation": ("State-mutation coverage", "STATE_MUTATION"),
}


def _normalise_dimension_status(value: Any) -> str | None:
    status = str(value or "").upper()
    allowed = {"COVERED", "PARTIALLY_COVERED", "NOT_COVERED", "NOT_APPLICABLE", "NOT_EVALUABLE"}
    return status if status in allowed else None


def _dimension_status(category: str, declared_count: int, evaluable_count: int, explicit: Any = None) -> str:
    explicit_status = _normalise_dimension_status(explicit)
    if explicit_status:
        return explicit_status
    if declared_count <= 0:
        return "NOT_COVERED"
    if evaluable_count <= 0:
        return "NOT_EVALUABLE"
    if category == "NORMAL":
        return "COVERED"
    return "COVERED" if evaluable_count >= 2 else "PARTIALLY_COVERED"


def _build_g2_description(
    headline: str,
    suite_evidence: dict[str, Any] | None,
    test_report: dict[str, Any] | None,
) -> dict[str, Any]:
    evidence = suite_evidence or {}
    category_counts = {str(k).upper(): int(v or 0) for k, v in (evidence.get("category_counts") or {}).items()}
    declared_dimensions = evidence.get("declared_coverage_dimensions") or {}
    report_results = [
        item for item in ((test_report or {}).get("results", []) or [])
        if str(item.get("score_stream") or "CORE_BEHAVIOURAL").upper() == "CORE_BEHAVIOURAL"
    ]
    evaluable_by_category = Counter(
        str(item.get("category", "NORMAL")).upper()
        for item in report_results
        if item.get("status") in {"PASSED", "FAILED"}
    )
    passed_by_category = Counter(
        str(item.get("category", "NORMAL")).upper()
        for item in report_results
        if item.get("status") == "PASSED"
    )
    declared_total = int(evidence.get("core_test_count", evidence.get("test_count", 0)) or 0)
    evaluable_total = len(report_results)
    passed_total = sum(1 for item in report_results if item.get("status") == "PASSED")
    failed_total = sum(1 for item in report_results if item.get("status") not in {"PASSED", None})
    not_evaluable_total = max(declared_total - evaluable_total, 0)

    dimensions: dict[str, Any] = {}
    covered_names: list[str] = []
    partial_names: list[str] = []
    for key, (label, category) in _G2_DIMENSIONS.items():
        declared = category_counts.get(category, 0)
        evaluable = evaluable_by_category.get(category, 0)
        passed = passed_by_category.get(category, 0)
        explicit = declared_dimensions.get(key)
        if isinstance(explicit, dict):
            explicit = explicit.get("status")
        status = _dimension_status(category, declared, evaluable, explicit)
        if status == "COVERED":
            covered_names.append(label.lower())
        elif status == "PARTIALLY_COVERED":
            partial_names.append(label.lower())
        if declared == 0:
            evidence_text = f"No {category} test is declared in the common suite."
        elif evaluable == 0:
            evidence_text = f"{declared} {category} test(s) are declared, but none were evaluable in this run."
        else:
            evidence_text = f"{declared} {category} test(s) declared; {evaluable} evaluable; {passed} passed."
        dimensions[key] = {
            "label": label,
            "status": status,
            "tests_declared": declared,
            "tests_evaluable": evaluable,
            "tests_passed": passed,
            "evidence": evidence_text,
        }

    strengths: list[str] = []
    if covered_names:
        strengths.append("The suite provides direct behavioural evidence for " + ", ".join(covered_names) + ".")
    if partial_names:
        strengths.append("The suite provides some evidence for " + ", ".join(partial_names) + ", although coverage is incomplete.")
    seeded = int(evidence.get("seeded_test_count", 0) or 0)
    env_controlled = int(evidence.get("environment_controlled_test_count", 0) or 0)
    if seeded:
        strengths.append(f"{seeded} test(s) use deterministic random seeds, improving reproducibility of stochastic behaviour.")
    if env_controlled:
        strengths.append(f"{env_controlled} test(s) explicitly control environment variables, reducing environment-dependent variation.")
    if evaluable_total and passed_total == evaluable_total:
        strengths.append(f"All {evaluable_total} evaluable behavioural test(s) passed in this run.")
    elif evaluable_total:
        strengths.append(f"{passed_total} of {evaluable_total} evaluable behavioural test(s) passed in this run.")

    limitations = [str(v) for v in evidence.get("coverage_limitations", []) if str(v).strip()]
    if not_evaluable_total:
        limitations.append(f"{not_evaluable_total} declared behavioural test(s) were not evaluable in this run.")
    uncovered = [d["label"] for d in dimensions.values() if d["status"] == "NOT_COVERED"]
    if uncovered:
        limitations.append("No direct common-test evidence is declared for: " + ", ".join(uncovered) + ".")
    if not limitations and headline in {"PARTIAL", "LIMITED"}:
        limitations.append("The available common test suite does not demonstrate exhaustive behavioural coverage.")

    declared_summary = evidence.get("declared_evidence_summary")
    if declared_summary:
        summary = str(declared_summary)
        summary += f" Runtime evidence: {evaluable_total} of {declared_total} declared test(s) were evaluable and {passed_total} passed."
    elif declared_total:
        summary = (
            f"{declared_total} behavioural test(s) are declared; {evaluable_total} were evaluable in this run and "
            f"{passed_total} passed. The G2 headline classification is {headline}."
        )
    else:
        summary = "No common behavioural tests are declared, so behavioural evidence adequacy cannot be established."

    basis = evidence.get("coverage_basis") or (
        "Assessment is based on the declared common-test categories, criteria links, reproducibility controls, "
        "coverage limitations, and the tests that were actually evaluable and executed in this run."
    )
    guidance = evidence.get("interpretation_guidance")
    if guidance:
        interpretation = str(guidance)
    elif headline == "ADEQUATE":
        interpretation = (
            "The behavioural accuracy is supported by comparatively broad and reproducible evidence across the declared test scope. "
            "It should still be interpreted as evidence for the tested cases rather than proof over every possible input."
        )
    elif headline == "PARTIAL":
        interpretation = (
            "The behavioural accuracy provides useful evidence for the exercised behaviours, but important paths or conditions remain "
            "untested or only partly covered. It should not be interpreted as complete behavioural equivalence."
        )
    elif headline == "LIMITED":
        interpretation = (
            "The behavioural accuracy is supported by a narrow test scope. Treat it as evidence for the specific exercised scenario(s), "
            "not as strong evidence of general behavioural equivalence. Structural C/A/F/P evidence and human review remain important."
        )
    elif headline == "NOT_EVALUABLE":
        interpretation = "No defensible behavioural-evidence adequacy judgement can be made from the tests available to this run."
    else:
        interpretation = "The test suite did not declare an evidence-adequacy classification; interpret behavioural results cautiously."

    return {
        "summary": summary,
        "test_counts": {
            "declared": declared_total,
            "evaluable": evaluable_total,
            "passed": passed_total,
            "failed": failed_total,
            "not_evaluable": not_evaluable_total,
        },
        "coverage_dimensions": dimensions,
        "strengths": strengths,
        "limitations": limitations,
        "coverage_basis": str(basis),
        "interpretation": interpretation,
        "manual_review_targets": evidence.get("manual_review_targets", []),
        "reproducibility": {
            "seeded_test_count": seeded,
            "environment_controlled_test_count": env_controlled,
        },
    }


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _stage_status(pipeline_report: dict[str, Any] | None, name: str) -> str | None:
    if not pipeline_report:
        return None
    for stage in pipeline_report.get("stages", []):
        if stage.get("name") == name:
            return stage.get("status")
    return None


def _stage_message(pipeline_report: dict[str, Any] | None, name: str) -> str | None:
    if not pipeline_report:
        return None
    for stage in pipeline_report.get("stages", []):
        if stage.get("name") == name:
            return stage.get("message")
    return None


def _parser_stage(parser_report: dict[str, Any] | None, name: str) -> dict[str, Any] | None:
    if not parser_report:
        return None
    for stage in parser_report.get("stages", []):
        if stage.get("name") == name:
            return stage
    return None


def _criterion_template(stage_key: str, criterion_id: str) -> dict[str, Any]:
    stage = STAGES[stage_key]
    definition = next(c for c in stage["criteria"] if c["criterion_id"] == criterion_id)
    return {
        "criterion_id": criterion_id,
        "question": definition["question"],
        "maximum_score": 2,
        "critical_semantic_criterion": definition["critical_semantic_criterion"],
    }


def _assessment(
    stage_key: str,
    criterion_id: str,
    score: int | None,
    status: str,
    justification: str,
    rule_id: str,
    evidence: list[dict[str, Any]] | None = None,
    confidence: str = "HIGH",
) -> dict[str, Any]:
    item = _criterion_template(stage_key, criterion_id)
    item["automated_assessment"] = {
        "score": score,
        "status": status,
        "confidence": confidence,
        "justification": justification,
        "scoring_method": {
            "type": "AUTOMATED",
            "rule_id": rule_id,
        },
    }
    item["evidence"] = evidence or []
    item["human_assessment"] = {
        "completed": False,
        "score": None,
        "agreement_with_automated_score": None,
        "semantic_issue": None,
        "reviewer_justification": None,
    }
    return item


def _na(stage_key: str, criterion_id: str, reason: str, rule_id: str) -> dict[str, Any]:
    return _assessment(
        stage_key,
        criterion_id,
        None,
        "NOT_EVALUABLE",
        reason,
        rule_id,
        confidence="HIGH",
    )


def _stage_summary(criteria: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [
        c["automated_assessment"]["score"]
        for c in criteria
        if c["automated_assessment"]["score"] is not None
    ]
    maximum = len(scores) * 2
    obtained = sum(scores)
    percentage = round((obtained / maximum) * 100, 2) if maximum else None
    semantic_failure = any(
        c["critical_semantic_criterion"]
        and c["automated_assessment"]["score"] == 0
        for c in criteria
    )
    review_required = any(
        c["automated_assessment"]["status"] in {"REVIEW_REQUIRED", "PARTIAL"}
        or c["automated_assessment"]["confidence"] == "LOW"
        for c in criteria
    )
    if not scores:
        status = "NOT_EVALUABLE"
    elif semantic_failure:
        status = "SEMANTIC_FAILURE"
    elif review_required:
        status = "REVIEW_REQUIRED"
    elif percentage == 100:
        status = "PASS"
    else:
        status = "PARTIAL"
    return {
        "score_obtained": obtained if scores else None,
        "maximum_applicable_score": maximum if scores else None,
        "percentage": percentage,
        "semantic_failure": semantic_failure,
        "review_required": review_required,
        "status": status,
    }


def _flow_visual_ast_counts(flow: dict[str, Any]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for node in (flow.get("nodes") or {}).values():
        if not isinstance(node, dict):
            continue
        kind = (node.get("data") or {}).get("ast_kind")
        if kind in EXECUTABLE_KINDS:
            counts[kind] += 1
    return dict(sorted(counts.items()))


def _expected_executable_counts(structured_signature: dict[str, Any]) -> dict[str, int]:
    return {
        kind: count
        for kind, count in structured_signature.get("kinds", {}).items()
        if kind in EXECUTABLE_KINDS and count
    }


class StudyScoringEngine:
    """Scores one algorithm directory from its immutable pipeline artefacts."""

    def score(
        self,
        artifact_directory: Path,
        algorithm_metadata: dict[str, Any],
        benchmark: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        artifact_directory = Path(artifact_directory)
        pipeline_report = _read_json(artifact_directory / "pipeline_report.json")
        processing_report = _read_json(artifact_directory / "pseudocode_processing_report.json")
        parser_report = _read_json(artifact_directory / "parser_report.json")
        ast_document = _read_json(artifact_directory / "ast.json")
        flow_document = _read_json(artifact_directory / "flow_diagram.json")
        compilation_report = _read_json(artifact_directory / "compilation_report.json")
        test_report = _read_json(artifact_directory / "test_report.json")
        semantic_test_report = _read_json(artifact_directory / "semantic_test_report.json")
        test_suite_evidence = _read_json(artifact_directory / "test_suite_evidence.json")
        semantic_contract = deepcopy((test_suite_evidence or {}).get("semantic_contract"))
        use_semantic_behaviour = bool(not algorithm_metadata.get("is_baseline", False) and semantic_contract is not None and semantic_test_report is not None)
        behaviour_report = semantic_test_report if use_semantic_behaviour else test_report
        behaviour_artifact = "semantic_test_report.json" if use_semantic_behaviour else "test_report.json"
        flow_mediation = _read_json(artifact_directory / "flow_mediation_analysis.json")

        ast_signature = signature_from_ast_adjacency(ast_document) if ast_document else None
        structured_signature = None
        signature_comparison = None
        graph_validation = None
        complexity = None
        visual_ast_counts = None
        expected_exec_counts = None
        if flow_document and isinstance(flow_document.get("structured_program"), dict):
            structured_signature = signature_from_structured_program(flow_document["structured_program"])
            graph_validation = flow_graph_validation(flow_document)
            complexity = complexity_from_structured_program(flow_document["structured_program"])
            visual_ast_counts = _flow_visual_ast_counts(flow_document)
            expected_exec_counts = _expected_executable_counts(structured_signature)
            if ast_signature:
                signature_comparison = compare_signatures(ast_signature, structured_signature)

        # Source sufficiency gate: compiler-recognised unresolved abstractions are expected source failures.
        compilation_status = (compilation_report or {}).get("status") or _stage_status(
            pipeline_report, "FLOW_DIAGRAM_TO_PYTHON"
        )
        if compilation_status == "EXPECTED_FAILURE":
            g1_result = "EXPECTED_FAILURE"
            g1_justification = (
                (compilation_report or {}).get("message")
                or "The pipeline identified unresolved source abstractions and did not invent their semantics."
            )
        elif _stage_status(pipeline_report, "PSEUDOCODE_TO_AST") == "FAILURE":
            g1_result = "REVIEW_REQUIRED"
            g1_justification = (
                "The source did not reach a validated AST. A human reviewer must distinguish malformed/unsupported "
                "notation from genuine semantic underspecification."
            )
        else:
            g1_result = "EVALUABLE"
            g1_justification = "The available artefacts do not identify unresolved source semantics that require invention."

        source_gate = {
            **deepcopy(SOURCE_GATE),
            "result": g1_result,
            "automated": True,
            "justification": g1_justification,
            "human_assessment": {
                "completed": False,
                "result": None,
                "agreement_with_automated_result": None,
                "reviewer_justification": None,
            },
        }

        declared_g2 = str((test_suite_evidence or {}).get("declared_evidence_adequacy", "NOT_DECLARED")).upper()
        allowed_g2 = set(BEHAVIOURAL_EVIDENCE_GATE["allowed_results"])
        if declared_g2 not in allowed_g2:
            declared_g2 = "NOT_DECLARED"
        evidence_test_count = int((test_suite_evidence or {}).get("test_count", 0) or 0)
        if declared_g2 != "NOT_DECLARED":
            g2_result = declared_g2
            g2_justification = (
                f"The test-suite specification declares behavioural evidence adequacy as {declared_g2}."
            )
        elif evidence_test_count == 0:
            g2_result = "NOT_EVALUABLE"
            g2_justification = "No behavioural test suite was available for evidence-adequacy assessment."
        else:
            has_main = bool((test_suite_evidence or {}).get("has_normal_or_branch_test"))
            has_edge = bool((test_suite_evidence or {}).get("has_boundary_error_or_termination_test"))
            has_state = bool((test_suite_evidence or {}).get("has_state_mutation_test"))
            if has_main and has_edge and (evidence_test_count >= 3):
                g2_result = "ADEQUATE"
            elif has_main and (has_edge or has_state or evidence_test_count >= 2):
                g2_result = "PARTIAL"
            else:
                g2_result = "LIMITED"
            g2_justification = (
                "Evidence adequacy was inferred from available test categories because the suite did not declare it explicitly."
            )
        behavioural_evidence_gate = {
            **deepcopy(BEHAVIOURAL_EVIDENCE_GATE),
            "result": g2_result,
            "automated": True,
            "justification": g2_justification,
            "evidence": test_suite_evidence or {},
            "human_assessment": {
                "completed": False,
                "result": None,
                "agreement_with_automated_result": None,
                "reviewer_justification": None,
            },
        }

        # Canonicalisation
        c: list[dict[str, Any]] = []
        parse_status = _stage_status(pipeline_report, "PSEUDOCODE_TO_AST")
        if parse_status == "SUCCESS":
            c.append(_assessment(
                "canonicalisation", "C1", 2, "PASS",
                "Canonical AJ completed syntax/static validation and produced an AST.",
                "CANON_PARSE_SUCCESS_001",
                [{"artifact": "parser_report.json", "observed_value": "SUCCESS"}],
            ))
        elif parse_status == "FAILURE":
            c.append(_assessment(
                "canonicalisation", "C1", 0, "FAIL",
                "Canonical AJ did not produce a validated AST.",
                "CANON_PARSE_FAILURE_001",
                [{"artifact": "pipeline_report.json", "observed_value": "PSEUDOCODE_TO_AST=FAILURE"}],
            ))
        else:
            c.append(_na("canonicalisation", "C1", "No parser outcome artefact is available.", "CANON_PARSE_NA_001"))

        if processing_report is None:
            for cid in ("C2", "C3", "C4"):
                c.append(_na("canonicalisation", cid, "The pseudocode processing audit is unavailable.", f"{cid}_NO_AUDIT_001"))
        else:
            transformations = processing_report.get("transformations", [])
            semantic_changes = [t for t in transformations if t.get("semantic_change") is True]
            uncertain = [
                t for t in transformations
                if t.get("confidence") not in ACCEPTED_TRANSFORMATION_CONFIDENCE
            ]
            evidence = [{
                "artifact": "pseudocode_processing_report.json",
                "transformation_count": len(transformations),
                "semantic_change_count": len(semantic_changes),
                "uncertain_transformation_count": len(uncertain),
                "rule_families": sorted({str(t.get("rule_family")) for t in transformations}),
            }]
            if semantic_changes:
                c.append(_assessment(
                    "canonicalisation", "C2", 0, "FAIL",
                    "At least one processing audit record declares a semantic change.",
                    "CANON_OPERATION_PRESERVATION_001", evidence,
                ))
                c.append(_assessment(
                    "canonicalisation", "C3", 0, "FAIL",
                    "At least one processing audit record declares a semantic change capable of affecting source behaviour.",
                    "CANON_CONTROL_STATE_001", evidence,
                ))
                c.append(_assessment(
                    "canonicalisation", "C4", 0, "FAIL",
                    "The audit records a semantic change, so absence of semantic invention cannot be established.",
                    "CANON_NO_INVENTION_001", evidence,
                ))
            elif uncertain:
                for cid, text in (
                    ("C2", "No declared semantic change was found, but one or more transformation records use an unapproved evidence-confidence category."),
                    ("C3", "Control/state-changing transformations are not declared, but one or more transformation records require review."),
                    ("C4", "Absence of semantic invention cannot be established automatically for all transformation records."),
                ):
                    c.append(_assessment(
                        "canonicalisation", cid, 1, "REVIEW_REQUIRED", text,
                        f"CANON_REVIEW_{cid}_001", evidence, confidence="MEDIUM",
                    ))
            else:
                c.append(_assessment(
                    "canonicalisation", "C2", 2, "PASS",
                    "All logged transformations are from audited evidence categories and none declares a semantic change.",
                    "CANON_OPERATION_PRESERVATION_001", evidence,
                ))
                c.append(_assessment(
                    "canonicalisation", "C3", 2, "PASS",
                    "No logged transformation declares a change to control/state semantics; all transformations have accepted audit evidence.",
                    "CANON_CONTROL_STATE_001", evidence,
                ))
                c.append(_assessment(
                    "canonicalisation", "C4", 2, "PASS",
                    "No transformation is marked as semantic-changing and all transformations use accepted audit-evidence categories.",
                    "CANON_NO_INVENTION_001", evidence,
                ))

        # AST
        a: list[dict[str, Any]] = []
        if ast_document is None or parser_report is None:
            for cid in ("A1", "A2", "A3", "A4"):
                a.append(_na("ast", cid, "A validated AST/parser report is not available.", f"{cid}_NO_AST_001"))
        else:
            static = _parser_stage(parser_report, "STATIC_SEMANTIC_ANALYSIS") or {}
            static_status = static.get("status")
            warning_count = int((static.get("details") or {}).get("warning_count", 0) or 0)
            base_evidence = [{
                "artifact": "parser_report.json",
                "parser_success": bool(parser_report.get("success")),
                "static_semantic_status": static_status,
                "warning_count": warning_count,
            }, {
                "artifact": "ast.json",
                "node_count": (ast_signature or {}).get("node_count"),
                "operator_multiset": (ast_signature or {}).get("operators"),
            }]
            if parser_report.get("success"):
                a.append(_assessment(
                    "ast", "A1", 2, "PASS",
                    "The parser produced a complete adjacency AST after syntax and static-semantic analysis.",
                    "AST_CONSTRUCT_CORRESPONDENCE_001", base_evidence,
                ))
                expr_score = 2 if static_status == "SUCCESS" and warning_count == 0 else 1
                expr_status = "PASS" if expr_score == 2 else "REVIEW_REQUIRED"
                expr_conf = "MEDIUM" if expr_score == 2 else "LOW"
                a.append(_assessment(
                    "ast", "A2", expr_score, expr_status,
                    "Operator/literal relationships were accepted by syntax and static-semantic analysis. "
                    + ("No semantic warnings were reported." if warning_count == 0 else f"{warning_count} semantic warning(s) require review."),
                    "AST_EXPRESSION_ALIGNMENT_001", base_evidence, confidence=expr_conf,
                ))
                a.append(_assessment(
                    "ast", "A3", expr_score, expr_status,
                    "Control/scope relationships passed parser static-semantic analysis. "
                    + ("No semantic warnings were reported." if warning_count == 0 else f"{warning_count} semantic warning(s) require review."),
                    "AST_CONTROL_SCOPE_001", base_evidence, confidence=expr_conf,
                ))
                a.append(_assessment(
                    "ast", "A4", expr_score, expr_status,
                    "The canonical program was accepted as a semantically valid AST by the parser. "
                    "This automated judgement is retained for human verification rather than treated as an independent proof.",
                    "AST_SEMANTIC_EQUIVALENCE_001", base_evidence, confidence="MEDIUM",
                ))
            else:
                for cid in ("A1", "A2", "A3", "A4"):
                    a.append(_assessment(
                        "ast", cid, 0, "FAIL",
                        "Parser report records failure; AST semantic alignment was not established.",
                        f"{cid}_PARSER_FAILURE_001", base_evidence,
                    ))

        # Flow
        f: list[dict[str, Any]] = []
        if flow_document is None or structured_signature is None or ast_signature is None:
            for cid in ("F1", "F2", "F3", "F4"):
                f.append(_na("flow_diagram", cid, "Flow and/or AST evidence is unavailable.", f"{cid}_NO_FLOW_001"))
        else:
            counts_match = expected_exec_counts == visual_ast_counts
            signature_equal = bool(signature_comparison and signature_comparison.get("equivalent"))
            graph_valid = bool(graph_validation and graph_validation.get("valid"))
            graph_warnings = (graph_validation or {}).get("warnings", [])
            flow_evidence = [{
                "artifact": "flow_diagram.json",
                "expected_executable_ast_counts": expected_exec_counts,
                "visual_flow_ast_counts": visual_ast_counts,
                "graph_validation": graph_validation,
            }, {
                "artifact": "ast.json + flow_diagram.json:structured_program",
                "signature_comparison": signature_comparison,
            }]
            f.append(_assessment(
                "flow_diagram", "F1", 2 if counts_match else 0,
                "PASS" if counts_match else "FAIL",
                "Every executable AST construct has a corresponding visual flow node count." if counts_match
                else "Executable AST construct counts and visual flow-node construct counts differ.",
                "FLOW_NODE_COMPLETENESS_001", flow_evidence,
            ))
            if graph_valid and not graph_warnings:
                f2_score, f2_status, f2_conf = 2, "PASS", "HIGH"
                f2_text = "Flow graph entry/exit, edge references, decision out-degree and loop routing invariants passed."
            elif graph_valid:
                f2_score, f2_status, f2_conf = 1, "REVIEW_REQUIRED", "MEDIUM"
                f2_text = "Core flow graph invariants passed, but non-fatal graph warnings require human review."
            else:
                f2_score, f2_status, f2_conf = 0, "FAIL", "HIGH"
                f2_text = "One or more flow graph control-edge invariants failed."
            f.append(_assessment(
                "flow_diagram", "F2", f2_score, f2_status, f2_text,
                "FLOW_EDGE_CORRECTNESS_001", flow_evidence, confidence=f2_conf,
            ))
            f.append(_assessment(
                "flow_diagram", "F3", 2 if signature_equal and graph_valid else (1 if signature_equal else 0),
                "PASS" if signature_equal and graph_valid else ("REVIEW_REQUIRED" if signature_equal else "FAIL"),
                "The flow structured-program signature exactly matches the AST and graph invariants pass." if signature_equal and graph_valid
                else "AST/structured-program or graph-path evidence requires review.",
                "FLOW_PATH_EQUIVALENCE_001", flow_evidence,
                confidence="HIGH" if signature_equal and graph_valid else "MEDIUM",
            ))
            decision_expected = int(structured_signature.get("decision_count", 0))
            decision_visual = int((graph_validation or {}).get("decision_node_count", -1))
            decision_match = decision_expected == decision_visual and graph_valid
            f.append(_assessment(
                "flow_diagram", "F4", 2 if decision_match else (1 if graph_valid else 0),
                "PASS" if decision_match else ("REVIEW_REQUIRED" if graph_valid else "FAIL"),
                f"Structured AST contains {decision_expected} control decision(s); flow graph contains {decision_visual} decision node(s). "
                + ("Decision routing invariants passed." if decision_match else "Decision count/routing requires review."),
                "FLOW_DECISION_FIDELITY_001", flow_evidence,
                confidence="HIGH" if decision_match else "MEDIUM",
            ))

        # Python
        p: list[dict[str, Any]] = []
        if compilation_report is None:
            p.append(_na("python", "P1", "No compilation report is available.", "PY_EXECUTABILITY_NA_001"))
        elif compilation_status == "SUCCESS" and compilation_report.get("success"):
            p.append(_assessment(
                "python", "P1", 2, "PASS",
                "Python source was generated and syntax-validated by the compiler.",
                "PY_EXECUTABILITY_001",
                [{"artifact": "compilation_report.json", "status": compilation_status}],
            ))
        elif compilation_status == "EXPECTED_FAILURE":
            p.append(_na(
                "python", "P1",
                "No Python program was generated because unresolved source abstractions were deliberately preserved as an expected failure.",
                "PY_EXPECTED_FAILURE_001",
            ))
        else:
            p.append(_assessment(
                "python", "P1", 0, "FAIL",
                "Python compilation failed for a reason not classified as an expected unresolved-source failure.",
                "PY_EXECUTABILITY_001",
                [{"artifact": "compilation_report.json", "status": compilation_status}],
            ))

        if use_semantic_behaviour:
            total_tests = int((semantic_test_report or {}).get("evaluable_tests", 0) or 0)
            passed_tests = int((semantic_test_report or {}).get("passed_tests", 0) or 0)
        else:
            total_tests = int((test_report or {}).get("total_tests", 0) or 0)
            passed_tests = int((test_report or {}).get("passed_tests", 0) or 0)
        if total_tests:
            accuracy = (passed_tests / total_tests) * 100
            p2_score = 2 if passed_tests == total_tests else (1 if passed_tests else 0)
            p2_status = "PASS" if p2_score == 2 else ("PARTIAL" if p2_score == 1 else "FAIL")
            p.append(_assessment(
                "python", "P2", p2_score, p2_status,
                f"Generated Python passed {passed_tests} of {total_tests} " + ("task-semantic" if use_semantic_behaviour else "behavioural") + f" tests ({accuracy:.2f}%).",
                "PY_FUNCTIONAL_TESTS_001",
                [{"artifact": behaviour_artifact, "tests_total": total_tests, "tests_passed": passed_tests, "observation_mode": "TASK_SEMANTIC_FUNCTION" if use_semantic_behaviour else "PROGRAM_STDOUT_REFERENCE"}],
            ))
        else:
            p.append(_na("python", "P2", "No behavioural tests were executed for this algorithm.", "PY_FUNCTIONAL_TESTS_NA_001"))

        boundary_results = []
        if behaviour_report:
            boundary_results = [
                result for result in behaviour_report.get("results", [])
                if result.get("status") in {"PASSED", "FAILED"}
                and str(result.get("score_stream") or "CORE_BEHAVIOURAL").upper() == "CORE_BEHAVIOURAL"
                and str(result.get("category", "NORMAL")).upper() in {"BOUNDARY", "ERROR_BEHAVIOUR", "TERMINATION"}
            ]
        if boundary_results:
            boundary_passed = sum(r.get("status") == "PASSED" for r in boundary_results)
            p3_score = 2 if boundary_passed == len(boundary_results) else (1 if boundary_passed else 0)
            p.append(_assessment(
                "python", "P3", p3_score,
                "PASS" if p3_score == 2 else ("PARTIAL" if p3_score == 1 else "FAIL"),
                f"Passed {boundary_passed} of {len(boundary_results)} boundary/error/termination tests.",
                "PY_BOUNDARY_ERROR_001",
                [{"artifact": behaviour_artifact, "boundary_tests": len(boundary_results), "passed": boundary_passed}],
            ))
        else:
            p.append(_na(
                "python", "P3",
                "No tests are tagged BOUNDARY, ERROR_BEHAVIOUR or TERMINATION, so boundary/error/termination preservation cannot be scored automatically.",
                "PY_BOUNDARY_ERROR_NA_001",
            ))

        if compilation_status == "EXPECTED_FAILURE":
            p.append(_na(
                "python", "P4",
                "No generated Python exists because the source contained unresolved abstractions; semantic invention was intentionally avoided.",
                "PY_SEMANTIC_PRESERVATION_EXPECTED_FAILURE_001",
            ))
        elif compilation_status != "SUCCESS":
            p.append(_assessment(
                "python", "P4", 0, "FAIL",
                "A valid generated Python representation was not produced.",
                "PY_SEMANTIC_PRESERVATION_001",
            ))
        elif total_tests:
            if passed_tests == total_tests:
                p4_score, p4_status = 2, "PASS"
                p4_text = "Compilation succeeded and all available behavioural-oracle tests passed."
            elif passed_tests:
                p4_score, p4_status = 1, "PARTIAL"
                p4_text = "Compilation succeeded, but behavioural evidence is only partially correct."
            else:
                p4_score, p4_status = 0, "FAIL"
                p4_text = "Compilation succeeded, but none of the available behavioural-oracle tests passed."
            p.append(_assessment(
                "python", "P4", p4_score, p4_status, p4_text,
                "PY_SEMANTIC_PRESERVATION_001",
                [{"artifact": "compilation_report.json + " + behaviour_artifact, "tests_total": total_tests, "tests_passed": passed_tests}],
                confidence="HIGH" if p4_score in {0, 2} else "MEDIUM",
            ))
        else:
            p.append(_assessment(
                "python", "P4", 1, "REVIEW_REQUIRED",
                "Python compilation succeeded, but no behavioural oracle was executed; full source-target semantic preservation requires human review.",
                "PY_SEMANTIC_PRESERVATION_NO_TESTS_001",
                [{"artifact": "compilation_report.json", "status": "SUCCESS"}],
                confidence="LOW",
            ))

        stage_documents = {}
        for key, criteria in (
            ("canonicalisation", c), ("ast", a), ("flow_diagram", f), ("python", p)
        ):
            definition = STAGES[key]
            stage_documents[key] = {
                "stage_id": definition["stage_id"],
                "stage_name": definition["stage_name"],
                "stage_description": definition["stage_description"],
                "criteria": criteria,
                "stage_summary": _stage_summary(criteria),
            }

        ast_pct = stage_documents["ast"]["stage_summary"]["percentage"]
        flow_pct = stage_documents["flow_diagram"]["stage_summary"]["percentage"]
        if ast_pct is None or flow_pct is None:
            flow_delta = None
            flow_effect = "NOT_EVALUABLE"
        else:
            flow_delta = round(flow_pct - ast_pct, 2)
            flow_effect = "IMPROVEMENT" if flow_delta > 0 else ("DEGRADATION" if flow_delta < 0 else "NO_CHANGE")

        first_loss = None
        taxonomy = None
        for stage_key, taxonomy_name in (
            ("canonicalisation", "CANONICALISATION_ERROR"),
            ("ast", "AST_SEMANTIC_ERROR"),
            ("flow_diagram", "FLOW_CONTROL_ERROR"),
            ("python", "PYTHON_OR_BEHAVIOURAL_ERROR"),
        ):
            stage = stage_documents[stage_key]
            failed = next(
                (
                    criterion for criterion in stage["criteria"]
                    if criterion["critical_semantic_criterion"]
                    and criterion["automated_assessment"]["score"] == 0
                ),
                None,
            )
            if failed:
                first_loss = {
                    "stage": stage["stage_name"],
                    "criterion": failed["criterion_id"],
                    "reason": failed["automated_assessment"]["justification"],
                }
                taxonomy = taxonomy_name
                break
        if first_loss is None and g1_result == "EXPECTED_FAILURE":
            taxonomy = "SOURCE_UNDERSPECIFIED"

        category_metrics: dict[str, dict[str, Any]] = {}
        criteria_link_metrics: dict[str, dict[str, Any]] = {}
        for test_result in (behaviour_report or {}).get("results", []):
            if str(test_result.get("score_stream") or "CORE_BEHAVIOURAL").upper() != "CORE_BEHAVIOURAL":
                continue
            if test_result.get("status") not in {"PASSED", "FAILED"}:
                continue
            category = str(test_result.get("category", "NORMAL")).upper()
            row = category_metrics.setdefault(category, {"tests_total": 0, "tests_passed": 0})
            row["tests_total"] += 1
            if test_result.get("status") == "PASSED":
                row["tests_passed"] += 1
            for criterion in test_result.get("criteria_links", []) or []:
                crow = criteria_link_metrics.setdefault(str(criterion), {"tests_total": 0, "tests_passed": 0})
                crow["tests_total"] += 1
                if test_result.get("status") == "PASSED":
                    crow["tests_passed"] += 1
        for metric in list(category_metrics.values()) + list(criteria_link_metrics.values()):
            total = metric["tests_total"]
            metric["accuracy_percentage"] = round((metric["tests_passed"] / total) * 100, 2) if total else None

        behavioural = {
            "tests_total": total_tests,
            "tests_passed": passed_tests,
            "tests_failed": max(total_tests - passed_tests, 0),
            "accuracy_percentage": round((passed_tests / total_tests) * 100, 2) if total_tests else None,
            "complete_correctness": (passed_tests == total_tests) if total_tests else None,
            "category_metrics": category_metrics,
            "criteria_link_metrics": criteria_link_metrics,
            "evidence_adequacy": g2_result,
            "observation_mode": "TASK_SEMANTIC_FUNCTION" if use_semantic_behaviour else "PROGRAM_STDOUT_REFERENCE",
            "semantic_contract_version": (semantic_contract or {}).get("contract_version") if semantic_contract else None,
            "semantic_tests_not_evaluable": int((semantic_test_report or {}).get("not_evaluable_tests", 0) or 0) if use_semantic_behaviour else None,
            "semantic_boundary": (semantic_test_report or {}).get("semantic_boundary") if use_semantic_behaviour else None,
            "pre_freeze_validation": (semantic_test_report or {}).get("pre_freeze_validation") if use_semantic_behaviour else None,
        }
        behavioural_evidence_gate.update(
            _build_g2_description(g2_result, test_suite_evidence, behaviour_report)
        )

        all_stage_criteria = [
            criterion
            for stage in stage_documents.values()
            for criterion in stage.get("criteria", [])
        ]
        automated_rubric_summary = _stage_summary(all_stage_criteria)
        automated_rubric_summary.update({
            "criteria_total": len(all_stage_criteria),
            "criteria_completed": len(all_stage_criteria),
            "complete": True,
        })

        result = {
            "scoring_schema_version": SCORING_SCHEMA_VERSION,
            "rubric_version": RUBRIC_VERSION,
            "pipeline_version": PIPELINE_VERSION,
            "language_version": LANGUAGE_VERSION,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "rubric": {"scale": deepcopy(SCALE)},
            "rubric_scores": {
                "automated": automated_rubric_summary,
                "human": {
                    "score_obtained": None,
                    "maximum_applicable_score": None,
                    "percentage": None,
                    "criteria_total": len(all_stage_criteria),
                    "criteria_completed": 0,
                    "complete": False,
                    "status": "PENDING",
                },
                "combined": {
                    "available": False,
                    "percentage": None,
                    "automated_weight": 0.5,
                    "human_weight": 0.5,
                    "method": "ARITHMETIC_MEAN_OF_AUTOMATED_AND_HUMAN_RUBRIC_PERCENTAGES",
                    "requires_complete_human_rubric": True,
                    "note": (
                        "The combined rubric score becomes available only after a complete human rubric review. "
                        "Behavioural metrics remain separate and are not included in this average."
                    ),
                },
            },
            "algorithm": deepcopy(algorithm_metadata),
            "source_sufficiency": source_gate,
            "behavioural_evidence_adequacy": behavioural_evidence_gate,
            "stages": stage_documents,
            "behavioural_testing": behavioural,
            "semantic_contract": semantic_contract,
            "semantic_behavioural_evidence": deepcopy(semantic_test_report) if semantic_test_report is not None else None,
            "benchmark": benchmark or {"is_baseline": bool(algorithm_metadata.get("is_baseline", False))},
            "derived_metrics": {
                "pre_flow_stage_percentage": ast_pct,
                "post_flow_stage_percentage": flow_pct,
                "stage_score_difference": flow_delta,
                "stage_score_effect": flow_effect,
                "flowchart_delta": flow_delta,
                "flowchart_effect": flow_effect,
                "flowchart_delta_note": (
                    "Legacy/descriptive difference between the AST and flow-stage rubric percentages; the stages use different questions. "
                    "Do not interpret this value as a causal accuracy benefit of flowcharts."
                ),
                "flow_mediation_delta": (flow_mediation or {}).get("flow_mediation_delta"),
                "flow_mediation_effect": (flow_mediation or {}).get("flow_mediation_effect", "NOT_EVALUABLE"),
                "direct_ast_test_accuracy_percentage": (flow_mediation or {}).get("direct_test_accuracy_percentage"),
                "flow_mediated_test_accuracy_percentage": (flow_mediation or {}).get("flow_mediated_test_accuracy_percentage"),
                "flow_structured_program_matches_direct_ast": (flow_mediation or {}).get("structured_program_match"),
                "direct_vs_flow_python_source_match": (flow_mediation or {}).get("direct_vs_flow_python_source_match"),
                "flow_mediation_note": (flow_mediation or {}).get("interpretation"),
                "first_semantic_loss": first_loss,
                "failure_taxonomy": taxonomy,
            },
            "complexity": complexity,
            "review": {
                "status": "PENDING_HUMAN_REVIEW",
                "reviewer_id": None,
                "reviewed_at_utc": None,
                "overall_reviewer_confidence": None,
            },
        }
        return result

    def write_outputs(
        self,
        artifact_directory: Path,
        algorithm_metadata: dict[str, Any],
        benchmark: dict[str, Any] | None = None,
    ) -> dict[str, Path]:
        artifact_directory = Path(artifact_directory)
        scoring_dir = artifact_directory / "scoring"
        scoring_dir.mkdir(parents=True, exist_ok=True)
        result = self.score(artifact_directory, algorithm_metadata, benchmark)

        automated_path = scoring_dir / "automated_score.json"
        automated_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

        evidence = {
            "scoring_schema_version": result["scoring_schema_version"],
            "rubric_version": result["rubric_version"],
            "algorithm": result["algorithm"],
            "criterion_evidence": [
                {
                    "criterion_id": criterion["criterion_id"],
                    "question": criterion["question"],
                    "score": criterion["automated_assessment"]["score"],
                    "status": criterion["automated_assessment"]["status"],
                    "justification": criterion["automated_assessment"]["justification"],
                    "evidence": criterion["evidence"],
                }
                for stage in result["stages"].values()
                for criterion in stage["criteria"]
            ],
        }
        evidence_path = scoring_dir / "scoring_evidence.json"
        evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

        final_result = deepcopy(result)
        final_result["score_status"] = "PROVISIONAL_AUTOMATED"
        final_result["adjudication"] = {
            "human_review_completed": False,
            "criteria_total": (result.get("rubric_scores", {}).get("automated", {}) or {}).get("criteria_total"),
            "criteria_compared": 0,
            "criteria_agreed": 0,
            "agreement_percentage": None,
            "final_score_source": "AUTOMATED_WITH_HUMAN_REVIEW_PENDING_OR_PARTIAL",
            "criterion_substitution_used": False,
            "combined_rubric_percentage": None,
            "note": (
                "Automated scores remain unchanged. A complete human rubric review is retained as a parallel stream; "
                "the final combined rubric percentage is the equal-weight mean of the two overall rubric percentages."
            ),
        }
        final_path = scoring_dir / "final_score.json"
        final_path.write_text(json.dumps(final_result, indent=2), encoding="utf-8")

        return {
            "automated_score": automated_path,
            "scoring_evidence": evidence_path,
            "final_score": final_path,
        }
