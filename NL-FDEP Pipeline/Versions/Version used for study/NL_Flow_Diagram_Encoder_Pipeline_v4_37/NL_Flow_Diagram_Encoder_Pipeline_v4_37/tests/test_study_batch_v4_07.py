import json
import tempfile
import unittest
from pathlib import Path

from adjudication import adjudicate_files
from pseudocode_profiles import PseudocodeProfile
from study_batch import StudyBatchProcessor, StudyFolderError, discover_algorithm_folders


SAMPLE = """\
total <- INTEGER(0)
FOR i <- IN RANGE INTEGER(1) TO INTEGER(4) DO
    total <- total + i
ENDFOR
OUTPUT total
"""


class StudyBatchV407Tests(unittest.TestCase):
    def test_llm_results_batch_discovers_numeric_algorithm_folders_and_writes_local_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source_a" / "results"
            for number in (10, 2, 1):
                folder = root / f"Algorithm - {number}"
                folder.mkdir(parents=True)
                (folder / f"Algorithm {number} Pseudocode.txt").write_text(SAMPLE, encoding="utf-8")

            discovered = discover_algorithm_folders(root)
            self.assertEqual([1, 2, 10], [number for number, _ in discovered])

            report = StudyBatchProcessor().process_llm_results(
                root,
                profile=PseudocodeProfile.AJ_DIALECT_STRICT,
            )

            self.assertEqual(3, report["report"]["algorithm_count"])
            for number in (1, 2, 10):
                artifacts = root / f"Algorithm - {number}" / "pipeline_artifacts"
                self.assertTrue((artifacts / "manifest.json").exists())
                self.assertTrue((artifacts / "pipeline_report.json").exists())
                self.assertTrue((artifacts / "scoring" / "automated_score.json").exists())
                self.assertTrue((artifacts / "scoring" / "human_review_questionnaire.html").exists())
            self.assertTrue((root / "study_analysis" / "algorithm_scores.csv").exists())

    def test_study_analysis_preserves_run_history_and_latest_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source_a" / "results"
            folder = root / "Algorithm - 1"
            folder.mkdir(parents=True)
            (folder / "Algorithm 1 Pseudocode.txt").write_text(SAMPLE, encoding="utf-8")

            first = StudyBatchProcessor().process_llm_results(
                root, profile=PseudocodeProfile.AJ_DIALECT_STRICT
            )
            second = StudyBatchProcessor().process_llm_results(
                root, profile=PseudocodeProfile.AJ_DIALECT_STRICT
            )

            analysis = root / "study_analysis"
            histories = sorted((analysis / "run_history").iterdir())
            self.assertEqual(2, len(histories))
            self.assertNotEqual(first["report"]["batch_run_id"], second["report"]["batch_run_id"])
            self.assertEqual("4.37", second["report"]["pipeline_version"])
            self.assertEqual("1.5", second["report"]["batch_schema_version"])
            self.assertTrue((analysis / "batch_report.json").exists())
            self.assertTrue((analysis / "latest_run.json").exists())
            for history in histories:
                self.assertTrue((history / "batch_report.json").exists())
                self.assertTrue((history / "algorithm_scores.csv").exists())
                self.assertTrue((history / "run_metadata.json").exists())

    def test_baseline_uses_reference_python_as_oracle_when_expected_output_is_omitted(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "Baseline"
            pseudo = baseline / "pseudocode" / "Algorithm - 1"
            python = baseline / "python" / "Algorithm - 1"
            pseudo.mkdir(parents=True)
            python.mkdir(parents=True)
            (pseudo / "Algorithm 1 Pseudocode.txt").write_text(SAMPLE, encoding="utf-8")
            (python / "Algorithm 1 Python.py").write_text(
                "total=0\nfor i in range(1,4):\n    total += i\nprint(total)\n",
                encoding="utf-8",
            )
            (python / "Algorithm 1 Tests.json").write_text(
                json.dumps({"tests": [{"name": "reference_validation", "standard_input": [], "expected_output": ["6"]}, {"name": "reference_oracle", "standard_input": []}]}),
                encoding="utf-8",
            )

            report = StudyBatchProcessor().process_baseline(
                baseline,
                profile=PseudocodeProfile.AJ_DIALECT_STRICT,
            )

            self.assertEqual({"SUCCESS": 1}, report["report"]["status_counts"])
            artifacts = pseudo / "pipeline_artifacts"
            comparison = json.loads((artifacts / "baseline_python_comparison.json").read_text(encoding="utf-8"))
            self.assertEqual(100.0, comparison["behavioural_agreement_percentage"])
            score = json.loads((artifacts / "scoring" / "automated_score.json").read_text(encoding="utf-8"))
            self.assertEqual(100.0, score["behavioural_testing"]["accuracy_percentage"])
            self.assertEqual("Algorithm 1 Pseudocode.txt", score["algorithm"]["source_file"])

    def test_completed_human_review_is_adjudicated_without_overwriting_automated_score(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source_a" / "results"
            folder = root / "Algorithm - 1"
            folder.mkdir(parents=True)
            (folder / "Algorithm 1 Pseudocode.txt").write_text(SAMPLE, encoding="utf-8")
            StudyBatchProcessor().process_llm_results(root, profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            scoring = folder / "pipeline_artifacts" / "scoring"
            questionnaire = json.loads((scoring / "human_review_questionnaire.json").read_text(encoding="utf-8"))
            questionnaire["reviewer"]["reviewer_id"] = "R1"
            questionnaire["criteria"][0]["human_assessment"].update({
                "score": 1,
                "score_label": "1",
                "agreement_with_automated_score": "DISAGREE",
                "semantic_issue": True,
                "reviewer_justification": "Manual review found a discrepancy.",
            })
            questionnaire["behavioural_evidence_adequacy"].update({
                "human_result": "LIMITED",
                "agreement_with_automated_result": "DISAGREE",
                "reviewer_justification": "The behavioural evidence is narrower than the automated headline suggests.",
            })
            (scoring / "human_review.json").write_text(json.dumps(questionnaire), encoding="utf-8")
            final_path = adjudicate_files(scoring)
            self.assertIsNotNone(final_path)
            automated = json.loads((scoring / "automated_score.json").read_text(encoding="utf-8"))
            final = json.loads((scoring / "final_score.json").read_text(encoding="utf-8"))
            self.assertEqual(2, automated["stages"]["canonicalisation"]["criteria"][0]["automated_assessment"]["score"])
            criterion = final["stages"]["canonicalisation"]["criteria"][0]
            self.assertEqual(2, criterion["automated_assessment"]["score"])
            self.assertEqual(1, criterion["human_assessment"]["score"])
            self.assertNotIn("final_assessment", criterion)
            self.assertEqual("LIMITED", final["behavioural_evidence_adequacy"]["human_assessment"]["result"])
            self.assertTrue(final["behavioural_evidence_adequacy"]["human_assessment"]["completed"])
            self.assertEqual("HUMAN_REVIEW_PARTIAL", final["score_status"])
            self.assertFalse(final["rubric_scores"]["combined"]["available"])

    def test_missing_expected_pseudocode_filename_is_recorded_as_batch_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source_a" / "results"
            folder = root / "Algorithm - 1"
            folder.mkdir(parents=True)
            (folder / "wrong.txt").write_text(SAMPLE, encoding="utf-8")
            report = StudyBatchProcessor().process_llm_results(root, profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            self.assertEqual({"FAILURE": 1}, report["report"]["status_counts"])
            self.assertIn("Algorithm 1 Pseudocode.txt", report["report"]["algorithms"][0]["error"])


if __name__ == "__main__":
    unittest.main()

class StudyScoringCoverageV407Tests(unittest.TestCase):
    def test_flow_scoring_counts_else_if_as_a_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source_a" / "results"
            folder = root / "Algorithm - 1"
            folder.mkdir(parents=True)
            (folder / "Algorithm 1 Pseudocode.txt").write_text(
                '''score <- INTEGER(65)\nIF score >= 70 THEN\n    OUTPUT STRING("D")\nELSE IF score >= 60 THEN\n    OUTPUT STRING("M")\nELSE\n    OUTPUT STRING("P")\nENDIF\n''',
                encoding="utf-8",
            )
            StudyBatchProcessor().process_llm_results(root, profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            score = json.loads((folder / "pipeline_artifacts" / "scoring" / "automated_score.json").read_text(encoding="utf-8"))
            flow = score["stages"]["flow_diagram"]
            self.assertEqual(100.0, flow["stage_summary"]["percentage"])
            self.assertEqual(2, flow["criteria"][3]["automated_assessment"]["score"])

    def test_expected_compiler_failure_is_not_misreported_as_python_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source_a" / "results"
            folder = root / "Algorithm - 1"
            folder.mkdir(parents=True)
            (folder / "Algorithm 1 Pseudocode.txt").write_text(
                '''FUNCTION clean ACCEPTS(c AS CHAR)\nRETURN CALL is_punctuation(c)\nENDFUNCTION\n''',
                encoding="utf-8",
            )
            report = StudyBatchProcessor().process_llm_results(root, profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            self.assertEqual({"EXPECTED_FAILURE": 1}, report["report"]["status_counts"])
            artifacts = folder / "pipeline_artifacts"
            self.assertFalse((artifacts / "generated_program.py").exists())
            score = json.loads((artifacts / "scoring" / "automated_score.json").read_text(encoding="utf-8"))
            self.assertEqual("EXPECTED_FAILURE", score["source_sufficiency"]["result"])
            self.assertEqual("NOT_EVALUABLE", score["stages"]["python"]["stage_summary"]["status"])

class WholeStudyAggregationV407Tests(unittest.TestCase):
    def test_whole_study_aggregation_combines_baseline_and_model_scores(self):
        from study_analysis import aggregate_study_root
        with tempfile.TemporaryDirectory() as directory:
            study = Path(directory)
            # Model run
            source_folder = study / "source_a" / "results" / "Algorithm - 1"
            source_folder.mkdir(parents=True)
            (source_folder / "Algorithm 1 Pseudocode.txt").write_text(SAMPLE, encoding="utf-8")
            StudyBatchProcessor().process_llm_results(source_folder.parent, profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            # Baseline run
            pseudo = study / "Baseline" / "pseudocode" / "Algorithm - 1"
            ref = study / "Baseline" / "python" / "Algorithm - 1"
            pseudo.mkdir(parents=True); ref.mkdir(parents=True)
            (pseudo / "Algorithm 1 Pseudocode.txt").write_text(SAMPLE, encoding="utf-8")
            (ref / "Algorithm 1 Python.py").write_text("total=0\nfor i in range(1,4): total += i\nprint(total)\n", encoding="utf-8")
            StudyBatchProcessor().process_baseline(study / "Baseline", profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            outputs = aggregate_study_root(study)
            rows = json.loads(Path(outputs["all_models_scores_json"]).read_text(encoding="utf-8"))
            self.assertEqual({"Baseline", "source_a"}, {row["Dataset"] for row in rows})
            self.assertTrue(Path(outputs["model_summary_csv"]).exists())
            self.assertTrue(Path(outputs["algorithm_difficulty_csv"]).exists())
