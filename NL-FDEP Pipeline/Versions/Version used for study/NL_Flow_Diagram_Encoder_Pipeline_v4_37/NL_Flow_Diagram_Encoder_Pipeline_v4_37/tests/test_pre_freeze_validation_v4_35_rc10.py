from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from baseline_benchmark import load_test_spec, load_test_suite_metadata
from common_test_resources import DEFAULT_COMMON_TESTS_ROOT, TEST_DESIGN_VERSION, TEST_SPEC_SCHEMA_VERSION, validate_common_test_pack
from semantic_evaluation import SemanticTestHarness
from study_batch import StudyBatchProcessor
from pseudocode_profiles import PseudocodeProfile


class PreFreezeValidationRC10Tests(unittest.TestCase):
    def test_active_pack_identity_and_stream_counts(self):
        self.assertEqual("1.4.2", TEST_DESIGN_VERSION)
        self.assertEqual("1.6", TEST_SPEC_SCHEMA_VERSION)
        status = validate_common_test_pack()
        self.assertTrue(status.complete)
        counts = {"CORE_BEHAVIOURAL": 0, "PRE_FREEZE_VALIDATION": 0, "SEMANTIC_BOUNDARY_PROBE": 0}
        for aid in range(1, 51):
            path = DEFAULT_COMMON_TESTS_ROOT / f"Algorithm - {aid}" / f"Algorithm {aid} Tests.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            for case in data["tests"]:
                stream = str(case.get("score_stream") or "CORE_BEHAVIOURAL").upper()
                counts[stream] = counts.get(stream, 0) + 1
        self.assertEqual(129, counts["CORE_BEHAVIOURAL"])  # 99 automated + 30 interaction/reference-only core cases
        self.assertEqual(8, counts["PRE_FREEZE_VALIDATION"])
        self.assertEqual(19, counts["SEMANTIC_BOUNDARY_PROBE"])

    def test_rc9_regression_cases_are_quarantined_not_deleted(self):
        expected = {
            12: {"1x1 square diagonal sum", "2x2 square diagonal sum"},
            44: {"singleton maximum subarray", "all-negative maximum subarray"},
            45: {"1x1 matrix addition", "rectangular equal-size matrix addition"},
            46: {"1x1 matrix multiplication", "identity matrix multiplication"},
        }
        for aid, names in expected.items():
            path = DEFAULT_COMMON_TESTS_ROOT / f"Algorithm - {aid}" / f"Algorithm {aid} Tests.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            provisional = {case["name"] for case in data["tests"] if case.get("score_stream") == "PRE_FREEZE_VALIDATION"}
            self.assertEqual(names, provisional)
            self.assertEqual("PARTIAL", data["evidence_adequacy"])
            for case in data["tests"]:
                if case["name"] in names:
                    self.assertEqual("PENDING_BASELINE_CONFIRMATION", case["validation_status"])
                    self.assertEqual("PROVISIONAL_PRE_FREEZE_VALUE", case["semantic_test"]["expectation_policy"])

    def test_provisional_failures_do_not_reduce_core_accuracy(self):
        with tempfile.TemporaryDirectory() as td:
            program = Path(td) / "program.py"
            program.write_text(
                "def diagonal(matrix, n=None):\n"
                "    if len(matrix) <= 2: return -999\n"
                "    return sum(matrix[i][i] for i in range(len(matrix)))\n",
                encoding="utf-8",
            )
            suite = DEFAULT_COMMON_TESTS_ROOT / "Algorithm - 12" / "Algorithm 12 Tests.json"
            report = SemanticTestHarness().run(program, 12, load_test_suite_metadata(suite), load_test_spec(suite))
            self.assertEqual(3, report.evaluable_tests)
            self.assertEqual(3, report.passed_tests)
            self.assertEqual(100.0, report.accuracy_percentage)
            self.assertEqual(2, report.provisional_evaluable)
            self.assertEqual(0, report.provisional_passed)
            self.assertEqual(2, report.provisional_failed)
            self.assertEqual(0.0, report.provisional_accuracy_percentage)
            payload = report.to_dict()
            self.assertFalse(payload["pre_freeze_validation"]["included_in_core_behavioural_score"])
            self.assertFalse(payload["pre_freeze_validation"]["included_in_baseline_calibration"])

    def test_baseline_pipeline_excludes_provisional_cases_from_calibration(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            baseline = root / "Baseline"
            pseudo = baseline / "pseudocode" / "Algorithm - 1"
            python = baseline / "python" / "Algorithm - 1"
            pack = root / "common"
            pseudo.mkdir(parents=True)
            python.mkdir(parents=True)
            pack.mkdir(parents=True)
            (pseudo / "Algorithm 1 Pseudocode.txt").write_text('OUTPUT STRING("ok")\n', encoding="utf-8")
            (python / "Algorithm 1 Baseline Python code.txt").write_text('print("ok")\n', encoding="utf-8")
            (pack / "Algorithm 1 Tests.json").write_text(json.dumps({
                "test_spec_schema_version": "1.6",
                "test_design_version": "1.4.2",
                "algorithm_id": 1,
                "evidence_adequacy": "PARTIAL",
                "evidence_summary": "Regression test pack.",
                "coverage_dimensions": {"normal_path": "COVERED"},
                "coverage_basis": "One frozen core case plus one quarantined case.",
                "interpretation_guidance": "Provisional case must not affect calibration.",
                "coverage_limitations": [],
                "tests": [
                    {"name": "core", "standard_input": [], "category": "NORMAL", "score_stream": "CORE_BEHAVIOURAL", "expected_output": ["ok"]},
                    {"name": "provisional deliberately wrong", "standard_input": [], "category": "BOUNDARY", "score_stream": "PRE_FREEZE_VALIDATION", "expected_output": ["wrong"]},
                ],
            }), encoding="utf-8")
            result = StudyBatchProcessor(common_tests_root=pack).process_baseline(
                baseline, profile=PseudocodeProfile.AJ_DIALECT_STRICT,
            )
            row = result["report"]["algorithms"][0]
            self.assertEqual("SUCCESS", row["status"])
            self.assertEqual(100.0, row["baseline_calibration_percentage"])

    def test_algorithm22_zero_factorial_remains_frozen_core(self):
        path = DEFAULT_COMMON_TESTS_ROOT / "Algorithm - 22" / "Algorithm 22 Tests.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        zero = next(case for case in data["tests"] if case["name"] == "factorial of zero")
        self.assertEqual("NON_NEGATIVE_INTEGER", data["semantic_contract"]["inputs"][0]["type"])
        self.assertEqual("CORE_BEHAVIOURAL", zero["score_stream"])
        self.assertEqual(1, zero["semantic_test"]["expected_semantic_result"])
        self.assertEqual("STATIC_FROZEN_VALUE", zero["semantic_test"]["expectation_policy"])


if __name__ == "__main__":
    unittest.main()
