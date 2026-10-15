"""Combine automated and human rubric streams without score substitution.

The human review is a parallel assessment stream.  Automated criterion scores are
never overwritten by human scores.  Once all sixteen human rubric criteria have
been completed (a numeric 0/1/2 score or an explicit NA), the overall combined
rubric percentage is the equal-weight arithmetic mean of the automated and human
rubric percentages.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


def _status_for_score(score: int | None, score_label: str | None, fallback: str | None = None) -> str:
    if score_label == "NA":
        return "NOT_EVALUABLE"
    if score is None:
        return fallback or "NOT_EVALUABLE"
    if score == 0:
        return "FAIL"
    if score == 1:
        return "PARTIAL"
    return "PASS"


def _stream_summary(
    criteria: list[dict[str, Any]],
    *,
    assessment_key: str,
    human_stream: bool = False,
) -> dict[str, Any]:
    values: list[int] = []
    semantic_failure = False
    review_required = False
    completed = 0

    for criterion in criteria:
        assessment = criterion.get(assessment_key, {}) or {}
        if human_stream:
            is_completed = bool(assessment.get("completed"))
            if is_completed:
                completed += 1
            score = assessment.get("score") if is_completed else None
            score_label = assessment.get("score_label") if is_completed else None
            status = _status_for_score(score, score_label)
        else:
            completed += 1
            score = assessment.get("score")
            score_label = "NA" if score is None and assessment.get("status") == "NOT_EVALUABLE" else None
            status = str(assessment.get("status") or _status_for_score(score, score_label))

        if score is not None:
            values.append(int(score))
        if criterion.get("critical_semantic_criterion") and score == 0:
            semantic_failure = True
        if status in {"REVIEW_REQUIRED", "PARTIAL"}:
            review_required = True

    maximum = len(values) * 2
    obtained = sum(values)
    percentage = round(obtained / maximum * 100, 2) if maximum else None
    total = len(criteria)
    complete = completed == total if total else False

    if not values:
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
        "score_obtained": obtained if values else None,
        "maximum_applicable_score": maximum if values else None,
        "percentage": percentage,
        "semantic_failure": semantic_failure,
        "review_required": review_required,
        "status": status,
        "criteria_total": total,
        "criteria_completed": completed,
        "complete": complete,
    }


def _all_criteria(score: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        criterion
        for stage in score.get("stages", {}).values()
        for criterion in stage.get("criteria", [])
    ]


def _combined_percentage(automated_percentage: Any, human_percentage: Any, human_complete: bool) -> float | None:
    if not human_complete or automated_percentage is None or human_percentage is None:
        return None
    return round((float(automated_percentage) + float(human_percentage)) / 2.0, 2)


def _first_human_semantic_loss(score: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    for key, taxonomy in (
        ("canonicalisation", "CANONICALISATION_ERROR"),
        ("ast", "AST_SEMANTIC_ERROR"),
        ("flow_diagram", "FLOW_CONTROL_ERROR"),
        ("python", "PYTHON_OR_BEHAVIOURAL_ERROR"),
    ):
        stage = score.get("stages", {}).get(key, {})
        for criterion in stage.get("criteria", []):
            human = criterion.get("human_assessment", {}) or {}
            if criterion.get("critical_semantic_criterion") and human.get("completed") and human.get("score") == 0:
                return ({
                    "stage": stage.get("stage_name"),
                    "criterion": criterion.get("criterion_id"),
                    "reason": human.get("reviewer_justification"),
                }, taxonomy)
    return None, None


def adjudicate(automated: dict[str, Any], human: dict[str, Any]) -> dict[str, Any]:
    """Return a side-by-side automated/human score document with an equal-weight overall rubric score."""
    out = deepcopy(automated)
    human_by_id = {item.get("criterion_id"): item for item in human.get("criteria", [])}
    agreements = 0
    compared = 0

    for stage in out.get("stages", {}).values():
        for criterion in stage.get("criteria", []):
            cid = criterion.get("criterion_id")
            auto = criterion.get("automated_assessment", {}) or {}
            hitem = human_by_id.get(cid, {}) or {}
            h = hitem.get("human_assessment", {}) or {}
            human_label = h.get("score_label")
            human_score = h.get("score")
            human_completed = human_label is not None

            if human_completed:
                compared += 1
                agreement = h.get("agreement_with_automated_score")
                if agreement == "AGREE" or human_score == auto.get("score"):
                    agreements += 1

            auto_score = auto.get("score")
            criterion["human_assessment"] = {
                "completed": human_completed,
                "score": human_score,
                "score_label": human_label,
                "status": _status_for_score(human_score, human_label) if human_completed else "PENDING",
                "agreement_with_automated_score": h.get("agreement_with_automated_score"),
                "semantic_issue": h.get("semantic_issue"),
                "reviewer_justification": h.get("reviewer_justification"),
            }
            criterion["score_comparison"] = {
                "automated_score": auto_score,
                "human_score": human_score if human_completed else None,
                "human_completed": human_completed,
                "agreement": h.get("agreement_with_automated_score") if human_completed else None,
                "human_minus_automated": (
                    human_score - auto_score
                    if human_completed and human_score is not None and auto_score is not None
                    else None
                ),
                "note": "Criterion scores remain separate; the equal-weight combination is calculated at overall-rubric level only.",
            }
            # Remove any legacy substitution artefact if an older score document is re-adjudicated.
            criterion.pop("final_assessment", None)

        stage_criteria = stage.get("criteria", [])
        automated_summary = _stream_summary(stage_criteria, assessment_key="automated_assessment")
        human_summary = _stream_summary(stage_criteria, assessment_key="human_assessment", human_stream=True)
        stage["stage_summary"] = automated_summary  # legacy field remains the automated stream
        stage["automated_stage_summary"] = deepcopy(automated_summary)
        stage["human_stage_summary"] = human_summary
        stage["combined_stage_percentage"] = _combined_percentage(
            automated_summary.get("percentage"),
            human_summary.get("percentage"),
            bool(human_summary.get("complete")),
        )

    source_review = human.get("source_sufficiency", {}) or {}
    human_gate = source_review.get("human_result")
    out.setdefault("source_sufficiency", {})["human_assessment"] = {
        "completed": bool(human_gate),
        "result": human_gate,
        "agreement_with_automated_result": source_review.get("agreement_with_automated_result"),
        "reviewer_justification": source_review.get("reviewer_justification"),
    }
    out["source_sufficiency"]["comparison_note"] = (
        "Automated and human gate results are retained side by side; the human result does not replace the automated result."
    )
    out["source_sufficiency"].pop("final_result", None)

    evidence_review = human.get("behavioural_evidence_adequacy", {}) or {}
    human_g2 = evidence_review.get("human_result")
    if out.get("behavioural_evidence_adequacy") is not None:
        out["behavioural_evidence_adequacy"]["human_assessment"] = {
            "completed": bool(human_g2),
            "result": human_g2,
            "agreement_with_automated_result": evidence_review.get("agreement_with_automated_result"),
            "reviewer_justification": evidence_review.get("reviewer_justification"),
        }
        out["behavioural_evidence_adequacy"]["comparison_note"] = (
            "G2 is descriptive evidence adequacy and is not included in the combined rubric percentage."
        )
        out["behavioural_evidence_adequacy"].pop("final_result", None)

    # Preserve the automated derived metrics unchanged and add a parallel human-review metric block.
    human_first, human_taxonomy = _first_human_semantic_loss(out)
    human_ast = (out.get("stages", {}).get("ast", {}).get("human_stage_summary") or {}).get("percentage")
    human_flow = (out.get("stages", {}).get("flow_diagram", {}).get("human_stage_summary") or {}).get("percentage")
    if human_ast is None or human_flow is None:
        human_flow_delta = None
        human_flow_effect = "NOT_EVALUABLE"
    else:
        human_flow_delta = round(human_flow - human_ast, 2)
        human_flow_effect = "IMPROVEMENT" if human_flow_delta > 0 else ("DEGRADATION" if human_flow_delta < 0 else "NO_CHANGE")
    out["human_review_metrics"] = {
        "pre_flow_stage_percentage": human_ast,
        "post_flow_stage_percentage": human_flow,
        "flowchart_delta": human_flow_delta,
        "flowchart_effect": human_flow_effect,
        "first_semantic_loss": human_first,
        "failure_taxonomy": human_taxonomy,
    }
    out.setdefault("derived_metrics", {})["automated_human_agreement_percentage"] = (
        round(agreements / compared * 100, 2) if compared else None
    )

    criteria = _all_criteria(out)
    automated_overall = _stream_summary(criteria, assessment_key="automated_assessment")
    human_overall = _stream_summary(criteria, assessment_key="human_assessment", human_stream=True)
    combined_percentage = _combined_percentage(
        automated_overall.get("percentage"),
        human_overall.get("percentage"),
        bool(human_overall.get("complete")),
    )
    out["rubric_scores"] = {
        "automated": automated_overall,
        "human": human_overall,
        "combined": {
            "available": combined_percentage is not None,
            "percentage": combined_percentage,
            "automated_weight": 0.5,
            "human_weight": 0.5,
            "method": "ARITHMETIC_MEAN_OF_AUTOMATED_AND_HUMAN_RUBRIC_PERCENTAGES",
            "requires_complete_human_rubric": True,
            "note": (
                "The combined rubric score is 50% automated rubric percentage + 50% human rubric percentage. "
                "Mean semantic behavioural score and aggregate Common Test accuracy remain separate behavioural metrics and are not part of this average."
            ),
        },
    }

    total_criteria = human_overall.get("criteria_total", 0)
    completed_criteria = human_overall.get("criteria_completed", 0)
    human_complete = bool(human_overall.get("complete"))
    if human_complete:
        review_status = "COMPLETED"
        score_status = "AUTOMATED_HUMAN_COMBINED" if combined_percentage is not None else "HUMAN_REVIEW_COMPLETE_NOT_EVALUABLE"
    elif completed_criteria:
        review_status = "PARTIAL"
        score_status = "HUMAN_REVIEW_PARTIAL"
    else:
        review_status = "EMPTY"
        score_status = "PROVISIONAL_AUTOMATED"

    out["review"] = {
        "status": review_status,
        "reviewer_id": (human.get("reviewer") or {}).get("reviewer_id"),
        "reviewed_at_utc": (human.get("reviewer") or {}).get("reviewed_at_utc"),
        "overall_reviewer_confidence": (human.get("reviewer") or {}).get("overall_reviewer_confidence"),
        "overall_review": human.get("overall_review"),
    }
    out["score_status"] = score_status
    out["adjudication"] = {
        "human_review_completed": human_complete,
        "criteria_total": total_criteria,
        "criteria_compared": compared,
        "criteria_agreed": agreements,
        "agreement_percentage": round(agreements / compared * 100, 2) if compared else None,
        "final_score_source": (
            "EQUAL_WEIGHT_AUTOMATED_AND_HUMAN_RUBRIC_PERCENTAGES" if combined_percentage is not None
            else ("NO_COMBINED_RUBRIC_PERCENTAGE_AVAILABLE" if human_complete else "AUTOMATED_WITH_HUMAN_REVIEW_PENDING_OR_PARTIAL")
        ),
        "criterion_substitution_used": False,
        "combined_rubric_percentage": combined_percentage,
        "adjudicated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    return out


def adjudicate_files(scoring_directory: Path) -> Path | None:
    scoring_directory = Path(scoring_directory)
    auto_path = scoring_directory / "automated_score.json"
    human_path = scoring_directory / "human_review.json"
    if not auto_path.exists() or not human_path.exists():
        return None
    try:
        auto = json.loads(auto_path.read_text(encoding="utf-8"))
        human = json.loads(human_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    final = adjudicate(auto, human)
    final_path = scoring_directory / "final_score.json"
    final_path.write_text(json.dumps(final, indent=2), encoding="utf-8")
    return final_path
