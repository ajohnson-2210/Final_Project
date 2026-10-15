from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from baseline_benchmark import build_frozen_semantic_comparison, load_test_spec, load_test_suite_metadata
from common_test_resources import DEFAULT_COMMON_TESTS_ROOT, TEST_DESIGN_VERSION, TEST_SPEC_SCHEMA_VERSION, validate_common_test_pack
from human_review import HumanReviewQuestionnaireGenerator
from semantic_evaluation import SemanticTestHarness
from study_batch import expected_pseudocode_file


class SemanticCommonTestsV433Tests(unittest.TestCase):
    def test_pack_v14_has_50_contracts_156_cases_and_separate_boundary_stream(self):
        status = validate_common_test_pack()
        self.assertTrue(status.complete)
        self.assertEqual("1.4.2", TEST_DESIGN_VERSION)
        self.assertEqual("1.6", TEST_SPEC_SCHEMA_VERSION)
        self.assertEqual(50, status.suite_count)
        self.assertEqual(156, status.test_count)
        contracts = 0
        semantic = 0
        boundary_declared = 0
        boundary_enabled = 0
        provisional_declared = 0
        provisional_enabled = 0
        for aid in range(1, 51):
            path = DEFAULT_COMMON_TESTS_ROOT / f"Algorithm - {aid}" / f"Algorithm {aid} Tests.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            contracts += int(isinstance(data.get("semantic_contract"), dict))
            for case in data["tests"]:
                stream = str(case.get("score_stream") or "CORE_BEHAVIOURAL").upper()
                if stream == "SEMANTIC_BOUNDARY_PROBE":
                    boundary_declared += 1
                    boundary_enabled += int(bool((case.get("semantic_test") or {}).get("enabled")))
                elif stream == "PRE_FREEZE_VALIDATION":
                    provisional_declared += 1
                    provisional_enabled += int(bool((case.get("semantic_test") or {}).get("enabled")))
                else:
                    semantic += int(bool((case.get("semantic_test") or {}).get("enabled")))
        self.assertEqual(50, contracts)
        self.assertEqual(99, semantic)
        self.assertEqual(8, provisional_declared)
        self.assertEqual(8, provisional_enabled)
        self.assertEqual(19, boundary_declared)
        self.assertEqual(17, boundary_enabled)

    def test_algorithm1_semantic_observer_ignores_harmless_output_wording(self):
        with tempfile.TemporaryDirectory() as td:
            program = Path(td) / "program.py"
            program.write_text(
                "def unnamed_function(a,b):\n"
                "    print('The two strings are anagrams of each other' if sorted(a)==sorted(b) else 'No, these strings are not anagrams')\n",
                encoding="utf-8",
            )
            suite_path = DEFAULT_COMMON_TESTS_ROOT / "Algorithm - 1" / "Algorithm 1 Tests.json"
            report = SemanticTestHarness().run(program, 1, load_test_suite_metadata(suite_path), load_test_spec(suite_path))
            self.assertEqual(1, report.evaluable_tests)
            self.assertEqual(1, report.passed_tests)
            self.assertEqual(100.0, report.accuracy_percentage)

    def test_semantic_runtime_error_is_failed_not_not_evaluable(self):
        with tempfile.TemporaryDirectory() as td:
            program = Path(td) / "program.py"
            program.write_text("def unnamed_function(a,b):\n    raise TypeError('boom')\n", encoding="utf-8")
            suite_path = DEFAULT_COMMON_TESTS_ROOT / "Algorithm - 1" / "Algorithm 1 Tests.json"
            report = SemanticTestHarness().run(program, 1, load_test_suite_metadata(suite_path), load_test_spec(suite_path))
            self.assertEqual(1, report.evaluable_tests)
            self.assertEqual(1, report.failed_tests)
            self.assertEqual(0.0, report.accuracy_percentage)

    def test_whitespace_tolerant_pseudocode_filename_is_unambiguous(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td) / "Algorithm - 4"
            folder.mkdir()
            wanted = folder / "Algorithm 4  Pseudocode.txt"
            wanted.write_text("BEGIN\nEND\n", encoding="utf-8")
            self.assertEqual(wanted, expected_pseudocode_file(folder, 4))

    def test_semantic_comparison_uses_evaluable_semantic_denominator(self):
        comparison = build_frozen_semantic_comparison(
            semantic_test_report={"evaluable_tests": 4, "passed_tests": 3, "accuracy_percentage": 75.0},
            tests_path=DEFAULT_COMMON_TESTS_ROOT / "Algorithm - 1" / "Algorithm 1 Tests.json",
        )
        self.assertEqual("FROZEN_TASK_SEMANTIC", comparison["experimental_observation_mode"])
        self.assertEqual(75.0, comparison["experimental_behavioural_score_percentage"])
        self.assertEqual(-25.0, comparison["delta_from_frozen_reference_percentage_points"])
        self.assertEqual("BELOW_REFERENCE", comparison["comparison_to_frozen_reference"])
        self.assertFalse(comparison["runtime_baseline_reference_used"])

    def test_existing_human_questionnaire_contains_semantic_assessment_for_all_contract_runs(self):
        score = {
            "rubric_version": "1.1",
            "pipeline_version": "4.37",
            "algorithm": {"algorithm_id": 29, "dataset": "model", "source_file": "Algorithm 29 Pseudocode.txt"},
            "source_sufficiency": {"criterion_id": "G1", "question": "q", "result": "REVIEW_REQUIRED", "justification": "unsupported"},
            "behavioural_evidence_adequacy": {"criterion_id": "G2", "question": "q", "result": "NOT_EVALUABLE"},
            "semantic_contract": {"contract_version": "1.3", "task_statement": "Classify text", "automation_status": "HUMAN_SUPPORTED"},
            "semantic_behavioural_evidence": {"accuracy_percentage": None, "evaluable_tests": 0},
            "stages": {},
            "benchmark": {"is_baseline": False},
        }
        with tempfile.TemporaryDirectory() as td:
            paths = HumanReviewQuestionnaireGenerator().write(Path(td), score)
            data = json.loads(paths["questionnaire_json"].read_text(encoding="utf-8"))
            self.assertEqual("1.3", data["questionnaire_schema_version"])
            sem = data["task_semantic_evaluation"]
            self.assertEqual("1.3", sem["contract"]["contract_version"])
            self.assertIn("overall_semantic_assessment", sem["human_assessment"])
            html = paths["questionnaire_html"].read_text(encoding="utf-8")
            self.assertIn("Task-Semantic Evaluation", html)
            self.assertIn("Overall Semantic Assessment", html)


if __name__ == "__main__":
    unittest.main()
