import json
import tempfile
import unittest
from pathlib import Path

from aj_test_harness import AJTestHarness
from baseline_benchmark import test_cases_from_spec as build_test_cases
from pseudocode_profiles import PseudocodeProfile
from study_batch import StudyBatchProcessor
from study_analysis import aggregate_study_root


SAMPLE = """\
total <- INTEGER(0)
FOR i <- IN RANGE INTEGER(1) TO INTEGER(4) DO
    total <- total + i
ENDFOR
OUTPUT total
"""


class StudySafetyV418Tests(unittest.TestCase):
    def test_reprocessing_archives_previous_artifacts_and_prevents_stale_generated_python(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source_a" / "results"
            folder = root / "Algorithm - 1"
            folder.mkdir(parents=True)
            source = folder / "Algorithm 1 Pseudocode.txt"
            source.write_text(SAMPLE, encoding="utf-8")
            processor = StudyBatchProcessor()
            processor.process_llm_results(root, profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            artifacts = folder / "pipeline_artifacts"
            self.assertTrue((artifacts / "generated_program.py").exists())

            source.write_text("value <-\n", encoding="utf-8")
            second = processor.process_llm_results(root, profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            self.assertEqual("FAILURE", second["report"]["algorithms"][0]["status"])
            self.assertFalse((artifacts / "generated_program.py").exists())
            histories = list((artifacts / "run_history").glob("*/generated_program.py"))
            self.assertEqual(1, len(histories))

    def test_incomplete_current_run_is_reprocessed_not_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source_a" / "results"
            folder = root / "Algorithm - 1"
            folder.mkdir(parents=True)
            source = folder / "Algorithm 1 Pseudocode.txt"
            source.write_text(SAMPLE, encoding="utf-8")
            processor = StudyBatchProcessor()
            processor.process_llm_results(root, profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            artifacts = folder / "pipeline_artifacts"
            first_manifest = json.loads((artifacts / "manifest.json").read_text(encoding="utf-8"))
            (artifacts / "scoring" / "human_review_questionnaire.html").unlink()
            manifest = json.loads((artifacts / "manifest.json").read_text(encoding="utf-8"))
            manifest["processing_status"] = "RUNNING"
            manifest["completed_at_utc"] = None
            (artifacts / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

            second = processor.process_llm_results(root, profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            self.assertEqual("PROCESSED", second["report"]["algorithms"][0]["action"])
            new_manifest = json.loads((artifacts / "manifest.json").read_text(encoding="utf-8"))
            self.assertNotEqual(first_manifest["run_id"], new_manifest["run_id"])
            self.assertEqual("SUCCESS", new_manifest["processing_status"])

    def test_batch_failure_and_missing_folders_remain_in_algorithm_scores(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source_a" / "results"
            folder = root / "Algorithm - 1"
            folder.mkdir(parents=True)
            (folder / "wrong.txt").write_text(SAMPLE, encoding="utf-8")
            StudyBatchProcessor().process_llm_results(root, profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            rows = json.loads((root / "study_analysis" / "algorithm_scores.json").read_text(encoding="utf-8"))
            by_id = {row["Algorithm"]: row for row in rows}
            self.assertEqual(50, len(rows))
            self.assertFalse(by_id[1]["Scored"])
            self.assertEqual("FAILURE", by_id[1]["PipelineStatus"])
            self.assertFalse(by_id[2]["Scored"])
            self.assertEqual("PREFLIGHT_FAILURE", by_id[2]["BatchAction"])

    def test_baseline_pipeline_success_is_separate_from_calibration_status(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "Baseline"
            pseudo = baseline / "pseudocode" / "Algorithm - 1"
            py = baseline / "python" / "Algorithm - 1"
            pseudo.mkdir(parents=True); py.mkdir(parents=True)
            (pseudo / "Algorithm 1 Pseudocode.txt").write_text(SAMPLE, encoding="utf-8")
            (py / "Algorithm 1 Python.py").write_text("print('6')\n", encoding="utf-8")
            report = StudyBatchProcessor(common_tests_root=Path(directory) / "no_common_tests").process_baseline(baseline, profile=PseudocodeProfile.AJ_DIALECT_STRICT)["report"]
            self.assertEqual({"SUCCESS": 1}, report["pipeline_status_counts"])
            self.assertEqual({"BEHAVIOURAL_NOT_EVALUATED": 1}, report["calibration_status_counts"])

    def test_error_only_expectation_does_not_invent_zero_return_code_or_empty_output(self):
        with tempfile.TemporaryDirectory() as directory:
            program = Path(directory) / "program.py"
            program.write_text("raise ValueError('boom')\n", encoding="utf-8")
            cases, records = build_test_cases([{"name": "error", "expected_error_type": "ValueError"}])
            self.assertEqual(1, len(cases))
            self.assertIsNone(cases[0].expected_output)
            self.assertIsNone(cases[0].expected_return_code)
            report = AJTestHarness().run(program, cases)
            self.assertTrue(report.success)
            self.assertEqual("PASSED", report.results[0].status)
            self.assertEqual("RESEARCHER_VERIFIED", records[0]["expected_result_source"])

    def test_reference_timeout_does_not_create_default_expectations(self):
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / "reference.py"
            reference.write_text("import time\ntime.sleep(1)\n", encoding="utf-8")
            cases, records = build_test_cases([{"name": "timeout", "timeout_seconds": 0.05}], reference_python=reference)
            self.assertEqual([], cases)
            self.assertEqual("TIMEOUT", records[0]["reference"]["status"])
            self.assertEqual("NOT_EVALUABLE", records[0]["test_case_status"])

    def test_model_run_does_not_use_unvalidated_baseline_reference_as_oracle(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / "Baseline"
            bpython = base / "python" / "Algorithm - 1"
            bpseudo = base / "pseudocode" / "Algorithm - 1"
            bpython.mkdir(parents=True); bpseudo.mkdir(parents=True)
            (bpython / "Algorithm 1 Python.py").write_text("print('WRONG_ORACLE')\n", encoding="utf-8")
            (bpython / "Algorithm 1 Tests.json").write_text(json.dumps({"tests": [{"name": "derived_only"}]}), encoding="utf-8")
            root = Path(directory) / "source_a" / "results"
            folder = root / "Algorithm - 1"
            folder.mkdir(parents=True)
            (folder / "Algorithm 1 Pseudocode.txt").write_text(SAMPLE, encoding="utf-8")

            StudyBatchProcessor().process_llm_results(root, profile=PseudocodeProfile.AJ_DIALECT_STRICT, baseline_root=base)
            artifacts = folder / "pipeline_artifacts"
            score = json.loads((artifacts / "scoring" / "automated_score.json").read_text(encoding="utf-8"))
            benchmark = score["benchmark"]
            self.assertFalse(benchmark["runtime_baseline_reference_used"])
            self.assertIsNone(benchmark["reference_python"])
            self.assertEqual("STATIC_PREEXPERIMENT_EXPECTATIONS", benchmark["expected_value_policy"])
            self.assertFalse((artifacts / "test_report.json").exists())

    def test_stale_batch_failure_is_archived_after_successful_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source_a" / "results"
            folder = root / "Algorithm - 1"
            folder.mkdir(parents=True)
            wrong = folder / "wrong.txt"
            wrong.write_text(SAMPLE, encoding="utf-8")
            processor = StudyBatchProcessor()
            processor.process_llm_results(root, profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            artifacts = folder / "pipeline_artifacts"
            self.assertTrue((artifacts / "batch_failure.json").exists())
            wrong.rename(folder / "Algorithm 1 Pseudocode.txt")
            second = processor.process_llm_results(root, profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            self.assertEqual("SUCCESS", second["report"]["algorithms"][0]["status"])
            self.assertFalse((artifacts / "batch_failure.json").exists())
            self.assertTrue(list((artifacts / "run_history").glob("*/batch_failure.json")))

    def test_whole_study_summary_counts_unscored_algorithms(self):
        with tempfile.TemporaryDirectory() as directory:
            study = Path(directory)
            root = study / "source_a" / "results"
            folder = root / "Algorithm - 1"
            folder.mkdir(parents=True)
            (folder / "wrong.txt").write_text(SAMPLE, encoding="utf-8")
            StudyBatchProcessor().process_llm_results(root, profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            outputs = aggregate_study_root(study)
            rows = json.loads(Path(outputs["all_models_scores_json"]).read_text(encoding="utf-8"))
            self.assertEqual(50, len(rows))
            summary_text = Path(outputs["model_summary_csv"]).read_text(encoding="utf-8")
            self.assertIn("UnscoredAlgorithms", summary_text)


if __name__ == "__main__":
    unittest.main()
