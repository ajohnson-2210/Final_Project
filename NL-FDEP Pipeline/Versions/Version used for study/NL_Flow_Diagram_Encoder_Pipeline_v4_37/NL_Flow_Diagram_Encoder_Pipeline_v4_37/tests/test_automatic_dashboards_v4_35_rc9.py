from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dashboard_generation import generate_dashboards_for_completed_batch
from pseudocode_profiles import PseudocodeProfile
from study_batch import StudyBatchProcessor


SAMPLE = """\
BEGIN
    INPUT String1, String2
    IF LENGTH(String1) != LENGTH(String2) THEN
        OUTPUT "Not Anagrams"
    ELSE
        SORT characters of String1
        SORT characters of String2
        IF String1 = String2 THEN
            OUTPUT "Anagrams"
        ELSE
            OUTPUT "Not Anagrams"
        ENDIF
    ENDIF
END
"""


class AutomaticDashboardRC9Tests(unittest.TestCase):
    def test_completed_llm_batch_automatically_generates_batch_and_comparative_dashboards(self):
        with tempfile.TemporaryDirectory() as td:
            study = Path(td)
            results = study / "Agent A" / "Results"
            folder = results / "Algorithm - 1"
            folder.mkdir(parents=True)
            (folder / "Algorithm 1 Pseudocode.txt").write_text(SAMPLE, encoding="utf-8")

            result = StudyBatchProcessor().process_llm_results(
                results,
                profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
            )

            dashboards = result["dashboards"]
            self.assertEqual("GENERATED", dashboards["status"])
            self.assertEqual(1, dashboards["comparative_completed_agent_count"])
            batch_path = Path(dashboards["batch_dashboard"])
            comparative_path = Path(dashboards["comparative_dashboard"])
            self.assertTrue(batch_path.is_file())
            self.assertTrue(comparative_path.is_file())
            self.assertTrue((results / "study_analysis" / "dashboard_generation.json").is_file())
            self.assertEqual(study / "analysis" / "dashboards" / "Agent A" / "NL_FDEP_batch_dashboard.html", batch_path)
            self.assertEqual(study / "analysis" / "dashboards" / "NL_FDEP_comparative_dashboard.html", comparative_path)
            self.assertFalse((results / "study_analysis" / "dashboards").exists())

            batch_html = batch_path.read_text(encoding="utf-8")
            self.assertIn("Combined Behavioural Measure", batch_html)
            self.assertIn("Semantic Boundary Variance", batch_html)
            self.assertIn("window.copyCode", batch_html)
            self.assertIn("All 1 algorithms remain visible", batch_html)

            history = Path(result["history_directory"])
            self.assertTrue((history / "dashboard_generation.json").is_file())
            self.assertFalse((history / "dashboards").exists())


    def test_completed_study_refreshes_all_individual_dashboards_into_central_agent_folders(self):
        with tempfile.TemporaryDirectory() as td:
            study = Path(td)
            for name, folder_name in (("Agent A", "Results"), ("Agent B", "results")):
                results = study / name / folder_name
                analysis = results / "study_analysis"
                analysis.mkdir(parents=True)
                (analysis / "batch_report.json").write_text(json.dumps({
                    "batch_type": "LLM_RESULTS",
                    "dataset": name,
                    "algorithm_count": 50,
                    "algorithms": [],
                }), encoding="utf-8")
                (analysis / "algorithm_scores.json").write_text("[]", encoding="utf-8")
                legacy = analysis / "dashboards"
                legacy.mkdir()
                (legacy / "NL_FDEP_batch_dashboard.html").write_text("legacy", encoding="utf-8")

            baseline = study / "Baseline"
            (baseline / "pseudocode").mkdir(parents=True)
            baseline_analysis = baseline / "study_analysis"
            baseline_analysis.mkdir(parents=True)
            (baseline_analysis / "batch_report.json").write_text(json.dumps({
                "batch_type": "BASELINE",
                "dataset": "Baseline",
                "algorithms": [],
            }), encoding="utf-8")
            (baseline_analysis / "algorithm_scores.json").write_text("[]", encoding="utf-8")

            root = study / "Agent B" / "results"
            status = generate_dashboards_for_completed_batch(root, root / "study_analysis", "LLM_RESULTS")
            self.assertEqual("GENERATED", status["status"])
            for name in ("Agent A", "Agent B", "Baseline"):
                self.assertTrue((study / "analysis" / "dashboards" / name / "NL_FDEP_batch_dashboard.html").is_file())
            self.assertTrue((study / "analysis" / "dashboards" / "NL_FDEP_comparative_dashboard.html").is_file())
            self.assertFalse((study / "Agent A" / "Results" / "study_analysis" / "dashboards").exists())
            self.assertFalse((study / "Agent B" / "results" / "study_analysis" / "dashboards").exists())
            self.assertFalse((baseline_analysis / "dashboards").exists())


    def test_human_review_details_and_combined_dashboard_are_generated_from_saved_review_artefacts(self):
        with tempfile.TemporaryDirectory() as td:
            study = Path(td)
            results = study / "Agent Review" / "Results"
            analysis = results / "study_analysis"
            analysis.mkdir(parents=True)
            (analysis / "batch_report.json").write_text(json.dumps({
                "batch_type": "LLM_RESULTS",
                "dataset": "Agent Review",
                "algorithm_count": 50,
                "algorithms": [],
            }), encoding="utf-8")
            (analysis / "algorithm_scores.json").write_text("[]", encoding="utf-8")

            scoring = results / "Algorithm - 1" / "pipeline_artifacts" / "scoring"
            scoring.mkdir(parents=True)
            final_score = {
                "score_status": "AUTOMATED_HUMAN_COMBINED",
                "review": {
                    "status": "COMPLETED",
                    "reviewer_id": "REV001",
                    "reviewed_at_utc": "2026-10-04T12:00:00+00:00",
                    "overall_reviewer_confidence": "HIGH",
                },
                "rubric_scores": {
                    "automated": {"percentage": 75.0},
                    "human": {"percentage": 87.5, "criteria_total": 16, "criteria_completed": 16, "complete": True},
                    "combined": {"available": True, "percentage": 81.25},
                },
                "derived_metrics": {"automated_human_agreement_percentage": 75.0},
                "source_sufficiency": {"result": "SUFFICIENT", "human_assessment": {"result": "SUFFICIENT", "agreement_with_automated_result": "AGREE", "reviewer_justification": "Source sufficient."}},
                "behavioural_evidence_adequacy": {"result": "PARTIAL", "human_assessment": {"result": "PARTIAL", "agreement_with_automated_result": "AGREE", "reviewer_justification": "Evidence is partial."}},
                "stages": {
                    "canonicalisation": {
                        "stage_name": "Canonicalisation",
                        "human_stage_summary": {"percentage": 100.0},
                        "criteria": [{
                            "criterion_id": "C1",
                            "question": "Was source meaning preserved?",
                            "critical_semantic_criterion": True,
                            "automated_assessment": {"score": 2, "status": "PASS", "confidence": "HIGH", "justification": "Automated evidence."},
                            "human_assessment": {"completed": True, "score": 2, "score_label": "2", "status": "PASS", "agreement_with_automated_score": "AGREE", "semantic_issue": False, "reviewer_justification": "Human criterion justification."},
                        }],
                    }
                },
            }
            (scoring / "final_score.json").write_text(json.dumps(final_score), encoding="utf-8")
            human_review = {
                "reviewer": {"reviewer_id": "REV001", "reviewer_name": "Test Reviewer", "reviewed_at_utc": "2026-10-04T12:00:00+00:00", "overall_reviewer_confidence": "HIGH"},
                "source_sufficiency": {"human_result": "SUFFICIENT", "agreement_with_automated_result": "AGREE", "reviewer_justification": "Source sufficient."},
                "behavioural_evidence_adequacy": {"human_result": "PARTIAL", "agreement_with_automated_result": "AGREE", "reviewer_justification": "Evidence is partial."},
                "task_semantic_evaluation": {"human_assessment": {"required_inputs_represented": "YES", "core_algorithm_logic": "CORRECT", "required_output_semantics_represented": "YES", "edge_and_domain_handling": "PARTIAL", "overall_semantic_assessment": "MOSTLY_CORRECT", "reviewer_justification": "Semantic review note."}},
                "overall_review": {"material_semantic_error_not_captured": False, "first_semantic_loss_stage": "NONE", "final_python_behaviourally_faithful": True, "additional_observations": "Overall review note."},
            }
            (scoring / "human_review.json").write_text(json.dumps(human_review), encoding="utf-8")
            (scoring / "human_review_questionnaire.html").write_text("questionnaire", encoding="utf-8")

            status = generate_dashboards_for_completed_batch(results, analysis, "LLM_RESULTS")
            self.assertEqual("GENERATED", status["status"])
            human_path = Path(status["human_review_dashboard"])
            self.assertEqual(study / "analysis" / "dashboards" / "NL_FDEP_human_review_dashboard.html", human_path)
            self.assertTrue(human_path.is_file())
            batch_text = Path(status["batch_dashboard"]).read_text(encoding="utf-8")
            human_text = human_path.read_text(encoding="utf-8")
            for expected in ("Test Reviewer", "REV001", "Human criterion justification.", "Semantic review note.", "Overall review note."):
                self.assertIn(expected, batch_text)
                self.assertIn(expected, human_text)
            self.assertIn("Review completion", human_text)
            self.assertIn("Criterion agreement", human_text)
            self.assertIn("Reviewer summary", human_text)
            self.assertIn("Criterion-level human review analysis", human_text)
            self.assertEqual(1, status["human_reviewer_count"])


    def test_requested_comparative_dashboard_suite_is_generated_from_study_artefacts(self):
        with tempfile.TemporaryDirectory() as td:
            study = Path(td)
            results = study / "Agent Tabs" / "Results"
            analysis = results / "study_analysis"
            analysis.mkdir(parents=True)
            (analysis / "batch_report.json").write_text(json.dumps({
                "batch_type": "LLM_RESULTS",
                "dataset": "Agent Tabs",
                "algorithm_count": 50,
                "mean_experimental_behavioural_percentage": 75.0,
                "semantic_test_accuracy_percentage": 80.0,
                "algorithms": [{"algorithm_id": 1, "experimental_behavioural_percentage": 50.0, "status": "SUCCESS"}],
            }), encoding="utf-8")
            (analysis / "algorithm_scores.json").write_text(json.dumps([{
                "Algorithm": 1,
                "ExperimentalBehaviouralPercent": 50.0,
                "ComparisonToBaseline": "BELOW_REFERENCE",
                "PipelineStatus": "SUCCESS",
                "G2TestsDeclared": 1,
                "G2TestsEvaluable": 1,
                "G2TestsPassed": 1,
                "G2TestsNotEvaluable": 0,
            }]), encoding="utf-8")

            status = generate_dashboards_for_completed_batch(results, analysis, "LLM_RESULTS")
            expected = {
                "interactive_heatmap_dashboard": "NL_FDEP_comparative_dashboard.html",
                "comparative_radial_dashboard": "NL-FDEP Comparative Radial Dashboard.html",
                "radial_profiles_dashboard": "NL-FDEP All AI Agents - 50-Algorithm Radial Profiles.html",
                "final_scoring_dashboard": "NL-FDEP Final Scoring Dashboard.html",
            }
            for key, filename in expected.items():
                path = Path(status[key])
                self.assertTrue(path.is_file())
                self.assertEqual(study / "analysis" / "dashboards" / filename, path)

            comparative_path = Path(status["comparative_dashboard"])
            self.assertEqual(
                study / "analysis" / "dashboards" / "NL_FDEP_comparative_dashboard.html",
                comparative_path,
            )
            comparative_html = comparative_path.read_text(encoding="utf-8")
            self.assertIn("NL-FDEP Interactive Comparative Heat Map", comparative_html)
            self.assertIn("Behavioural ranking", comparative_html)
            self.assertIn("Algorithm inspection", comparative_html)
            self.assertIn("Agent Tabs", comparative_html)

            radial = Path(status["comparative_radial_dashboard"]).read_text(encoding="utf-8")
            self.assertIn("NL-FDEP Comparative Radial Dashboard", radial)
            self.assertIn("Comparison to frozen semantic reference", radial)
            self.assertIn("Pipeline outcomes", radial)
            self.assertIn("highest mean behavioural score", radial)
            self.assertIn("const highestMeanScore", radial)
            self.assertIn("Joint highest", radial)

            profiles = Path(status["radial_profiles_dashboard"]).read_text(encoding="utf-8")
            self.assertIn("NL-FDEP: All AI Agents — 50-Algorithm Radial Profiles", profiles)
            self.assertIn("Agent Tabs", profiles)

            final_scoring = Path(status["final_scoring_dashboard"]).read_text(encoding="utf-8")
            self.assertIn("NL-FDEP Final Scoring Dashboard", final_scoring)
            self.assertIn("Human review scores loaded from saved study artefacts", final_scoring)
            self.assertNotIn("Scores saved in browser local storage", final_scoring)
            self.assertNotIn("fillDemoBtn", final_scoring)

            compatibility_status_path = Path(status["interactive_heatmap_dashboard"])
            self.assertEqual(comparative_path, compatibility_status_path)
            self.assertFalse(
                (study / "analysis" / "dashboards" / "NL_FDEP_interactive_heatmap_dashboard_v5.html").exists()
            )

    def test_final_scoring_uses_zero_credit_only_for_explicit_completed_non_scorable_reviews(self):
        with tempfile.TemporaryDirectory() as td:
            study = Path(td)
            results = study / "Agent Human" / "Results"
            analysis = results / "study_analysis"
            analysis.mkdir(parents=True)
            (analysis / "batch_report.json").write_text(json.dumps({
                "batch_type": "LLM_RESULTS",
                "dataset": "Agent Human",
                "algorithm_count": 50,
                "mean_experimental_behavioural_percentage": 80.0,
                "semantic_test_accuracy_percentage": 70.0,
                "algorithms": [],
            }), encoding="utf-8")
            (analysis / "algorithm_scores.json").write_text("[]", encoding="utf-8")

            def write_completed_review(aid: int, percentage: float = 87.5) -> None:
                scoring = results / f"Algorithm - {aid}" / "pipeline_artifacts" / "scoring"
                scoring.mkdir(parents=True, exist_ok=True)
                (scoring / "final_score.json").write_text(json.dumps({
                    "score_status": "AUTOMATED_HUMAN_COMBINED",
                    "review": {"status": "COMPLETED"},
                    "rubric_scores": {
                        "human": {
                            "percentage": percentage,
                            "criteria_total": 16,
                            "criteria_completed": 16,
                            "complete": True,
                        },
                        "automated": {"percentage": 75.0},
                        "combined": {"available": True, "percentage": 81.25},
                    },
                }), encoding="utf-8")

            write_completed_review(1)
            status = generate_dashboards_for_completed_batch(results, analysis, "LLM_RESULTS")
            text = Path(status["final_scoring_dashboard"]).read_text(encoding="utf-8")
            self.assertIn("Human Review Overall — eligibility and missing-data rule", text)
            self.assertIn("failure-to-demonstrate", text)
            self.assertIn("HumanEval", text)
            self.assertIn("SWE-bench", text)
            self.assertIn('"humanReviewsCompleted":1', text)
            self.assertIn('"humanReviewsRequired":50', text)
            self.assertIn('"humanReviewsScored":1', text)
            self.assertIn('"humanReviewCoveragePercentage":2.0', text)
            self.assertIn('"humanScoreEligible":false', text)
            self.assertIn('"humanCompletedMeanDescriptive":87.5', text)
            self.assertIn('"humanScore":null', text)
            self.assertIn("FINAL RANKING WITHHELD", text)

            for aid in range(2, 50):
                write_completed_review(aid)

            # A genuinely completed non-scorable review is explicitly marked by
            # adjudication and contributes 0% while remaining in the fixed N=50
            # denominator. The numerical-only mean stays visible as an audit value.
            scoring_50 = results / "Algorithm - 50" / "pipeline_artifacts" / "scoring"
            scoring_50.mkdir(parents=True, exist_ok=True)
            non_scorable = {
                "score_status": "HUMAN_REVIEW_COMPLETE_NOT_EVALUABLE",
                "review": {"status": "COMPLETED"},
                "rubric_scores": {
                    "human": {
                        "percentage": None,
                        "status": "NOT_EVALUABLE",
                        "score_obtained": None,
                        "maximum_applicable_score": None,
                        "criteria_total": 16,
                        "criteria_completed": 16,
                        "complete": True,
                    },
                    "automated": {"percentage": 75.0},
                    "combined": {"available": False, "percentage": None},
                },
            }
            (scoring_50 / "final_score.json").write_text(json.dumps(non_scorable), encoding="utf-8")
            status = generate_dashboards_for_completed_batch(results, analysis, "LLM_RESULTS")
            text = Path(status["final_scoring_dashboard"]).read_text(encoding="utf-8")
            self.assertIn('"humanReviewsCompleted":50', text)
            self.assertIn('"humanReviewsScored":49', text)
            self.assertIn('"humanReviewsCompletedNonScorable":1', text)
            self.assertIn('"humanReviewsCompletedNonScorableIds":[50]', text)
            self.assertIn('"humanReviewsCompletedUnresolvedMissingScore":0', text)
            self.assertIn('"humanReviewsTerminalResolved":50', text)
            self.assertIn('"humanZeroCreditRuleApplied":true', text)
            self.assertIn('"humanZeroCreditCount":1', text)
            self.assertIn('"humanScoreEligibility":"ELIGIBLE_COMPLETE_N_OF_N_WITH_ZERO_CREDIT_NON_SCORABLE"', text)
            self.assertIn('"humanScoreEligible":true', text)
            self.assertIn('"humanScore":85.75', text)
            self.assertIn("Completed non-scorable → 0%", text)
            self.assertIn("FINAL RANKING ACTIVE", text)

            # A completed record with an unexplained missing percentage is not a
            # failure-to-demonstrate outcome and must never be silently set to zero.
            unresolved = dict(non_scorable)
            unresolved.pop("score_status", None)
            (scoring_50 / "final_score.json").write_text(json.dumps(unresolved), encoding="utf-8")
            status = generate_dashboards_for_completed_batch(results, analysis, "LLM_RESULTS")
            text = Path(status["final_scoring_dashboard"]).read_text(encoding="utf-8")
            self.assertIn('"humanReviewsCompleted":50', text)
            self.assertIn('"humanReviewsScored":49', text)
            self.assertIn('"humanReviewsCompletedNonScorable":0', text)
            self.assertIn('"humanReviewsCompletedUnresolvedMissingScore":1', text)
            self.assertIn('"humanReviewsCompletedUnresolvedMissingScoreIds":[50]', text)
            self.assertIn('"humanScoreEligibility":"WITHHELD_COMPLETED_REVIEW_WITH_UNRESOLVED_MISSING_HUMAN_RUBRIC"', text)
            self.assertIn('"humanScoreEligible":false', text)
            self.assertIn('"humanScore":null', text)
            self.assertIn("TECHNICAL/DATA MISSING HUMAN RUBRIC", text)
            self.assertIn("FINAL RANKING WITHHELD", text)

            write_completed_review(50)
            status = generate_dashboards_for_completed_batch(results, analysis, "LLM_RESULTS")
            text = Path(status["final_scoring_dashboard"]).read_text(encoding="utf-8")
            self.assertIn('"humanReviewsCompleted":50', text)
            self.assertIn('"humanReviewsScored":50', text)
            self.assertIn('"humanReviewsCompletedNonScorable":0', text)
            self.assertIn('"humanReviewsCompletedUnresolvedMissingScore":0', text)
            self.assertIn('"humanReviewCoveragePercentage":100.0', text)
            self.assertIn('"humanNumericScoreCoveragePercentage":100.0', text)
            self.assertIn('"humanTerminalOutcomeCoveragePercentage":100.0', text)
            self.assertIn('"humanScoreEligible":true', text)
            self.assertIn('"humanScore":87.5', text)
            self.assertIn("FINAL RANKING ACTIVE", text)

    def test_locked_legacy_dashboard_directory_does_not_abort_central_generation(self):
        with tempfile.TemporaryDirectory() as td:
            study = Path(td)
            results = study / "Agent Lock" / "Results"
            analysis = results / "study_analysis"
            legacy = analysis / "dashboards"
            legacy.mkdir(parents=True)
            (legacy / "old.html").write_text("legacy", encoding="utf-8")
            (analysis / "batch_report.json").write_text(json.dumps({
                "batch_type": "LLM_RESULTS", "dataset": "Agent Lock", "algorithms": []
            }), encoding="utf-8")
            (analysis / "algorithm_scores.json").write_text("[]", encoding="utf-8")
            with patch("dashboard_generation.shutil.rmtree", side_effect=PermissionError("locked")):
                status = generate_dashboards_for_completed_batch(results, analysis, "LLM_RESULTS")
            self.assertEqual("GENERATED", status["status"])
            self.assertTrue(Path(status["comparative_dashboard"]).is_file())

    def test_dashboard_failure_is_non_fatal_and_is_recorded(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "Agent A" / "Results"
            analysis = root / "study_analysis"
            analysis.mkdir(parents=True)
            (analysis / "batch_report.json").write_text(
                json.dumps({"batch_type": "LLM_RESULTS", "dataset": "Agent A", "algorithms": []}),
                encoding="utf-8",
            )
            with patch("dashboard_generation.generate_batch_dashboard", side_effect=RuntimeError("dashboard boom")):
                status = generate_dashboards_for_completed_batch(root, analysis, "LLM_RESULTS")
            self.assertEqual("FAILED", status["status"])
            self.assertIn("dashboard boom", status["error"])
            recorded = json.loads((analysis / "dashboard_generation.json").read_text(encoding="utf-8"))
            self.assertEqual("FAILED", recorded["status"])

    def test_comparative_dashboard_discovers_case_insensitive_results_siblings(self):
        with tempfile.TemporaryDirectory() as td:
            study = Path(td)
            for name, folder_name, mean_b, acc in (
                ("Agent A", "Results", 80.0, 90.0),
                ("Agent B", "results", 70.0, 80.0),
            ):
                analysis = study / name / folder_name / "study_analysis"
                analysis.mkdir(parents=True)
                (analysis / "batch_report.json").write_text(json.dumps({
                    "batch_type": "LLM_RESULTS",
                    "dataset": name,
                    "algorithm_count": 50,
                    "mean_experimental_behavioural_percentage": mean_b,
                    "semantic_test_accuracy_percentage": acc,
                    "algorithms": [],
                }), encoding="utf-8")
                (analysis / "algorithm_scores.json").write_text("[]", encoding="utf-8")

            root = study / "Agent B" / "results"
            status = generate_dashboards_for_completed_batch(root, root / "study_analysis", "LLM_RESULTS")
            self.assertEqual(2, status["comparative_completed_agent_count"])
            text = Path(status["comparative_dashboard"]).read_text(encoding="utf-8")
            self.assertIn("Agent A", text)
            self.assertIn("Agent B", text)
            # Combined behavioural measures are 85.00 and 75.00, so A ranks first.
            self.assertLess(text.find('Agent A'), text.find('Agent B'))


if __name__ == "__main__":
    unittest.main()
