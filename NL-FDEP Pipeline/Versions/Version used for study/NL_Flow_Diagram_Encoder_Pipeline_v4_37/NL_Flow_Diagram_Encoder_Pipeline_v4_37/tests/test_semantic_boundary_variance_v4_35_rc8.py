from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from baseline_benchmark import load_test_spec, load_test_suite_metadata
from common_test_resources import DEFAULT_COMMON_TESTS_ROOT, validate_common_test_pack
from semantic_evaluation import SemanticTestHarness


class SemanticBoundaryVarianceRC8Tests(unittest.TestCase):
    def test_pack_v14_is_complete(self):
        status = validate_common_test_pack()
        self.assertTrue(status.complete)
        self.assertEqual(50, status.suite_count)
        self.assertEqual(156, status.test_count)

    def test_factorial_zero_is_core_valid_and_negative_is_boundary_probe(self):
        suite = DEFAULT_COMMON_TESTS_ROOT / "Algorithm - 22" / "Algorithm 22 Tests.json"
        data = json.loads(suite.read_text(encoding="utf-8"))
        self.assertEqual("NON_NEGATIVE_INTEGER", data["semantic_contract"]["inputs"][0]["type"])
        zero = next(t for t in data["tests"] if t["name"] == "factorial of zero")
        self.assertEqual("CORE_BEHAVIOURAL", zero["score_stream"])
        self.assertTrue(zero["semantic_test"]["enabled"])
        self.assertEqual([0], zero["semantic_test"]["fixture"]["arguments"])
        self.assertEqual(1, zero["semantic_test"]["expected_semantic_result"])
        neg = next(t for t in data["tests"] if "negative integer outside factorial" in t["name"])
        self.assertEqual("SEMANTIC_BOUNDARY_PROBE", neg["score_stream"])
        self.assertEqual("BOUNDARY_OBSERVATION", neg["semantic_test"]["expectation_policy"])

    def test_boundary_probe_acceptance_does_not_change_core_accuracy(self):
        with tempfile.TemporaryDirectory() as td:
            program = Path(td) / "program.py"
            program.write_text(
                "def rotate(Matrix, N=None):\n"
                "    Matrix[:] = [list(row) for row in zip(*Matrix)]\n"
                "    for row in Matrix: row.reverse()\n"
                "    return Matrix\n",
                encoding="utf-8",
            )
            suite = DEFAULT_COMMON_TESTS_ROOT / "Algorithm - 27" / "Algorithm 27 Tests.json"
            report = SemanticTestHarness().run(program, 27, load_test_suite_metadata(suite), load_test_spec(suite))
            self.assertEqual(100.0, report.accuracy_percentage)
            self.assertGreaterEqual(report.boundary_probes_evaluable, 1)
            self.assertGreaterEqual(report.boundary_probes_accepted, 1)
            self.assertEqual(100.0, report.boundary_variance_percentage)

    def test_boundary_runtime_failure_is_observed_not_core_failed(self):
        with tempfile.TemporaryDirectory() as td:
            program = Path(td) / "program.py"
            program.write_text(
                "def f(n):\n"
                "    if n < 0: raise ValueError('negative')\n"
                "    return bin(n)[2:]\n",
                encoding="utf-8",
            )
            suite = DEFAULT_COMMON_TESTS_ROOT / "Algorithm - 2" / "Algorithm 2 Tests.json"
            report = SemanticTestHarness().run(program, 2, load_test_suite_metadata(suite), load_test_spec(suite))
            self.assertEqual(100.0, report.accuracy_percentage)
            self.assertEqual(1, report.boundary_probes_evaluable)
            self.assertEqual(0, report.boundary_probes_accepted)
            self.assertEqual(1, report.boundary_probes_incidental_failure)
            self.assertEqual(0.0, report.boundary_variance_percentage)

    def test_algorithm33_zero_is_core_not_error_behaviour(self):
        suite = DEFAULT_COMMON_TESTS_ROOT / "Algorithm - 33" / "Algorithm 33 Tests.json"
        data = json.loads(suite.read_text(encoding="utf-8"))
        zero = next(t for t in data["tests"] if t["name"] == "square root of zero")
        self.assertEqual("BOUNDARY", zero["category"])
        self.assertEqual(0, zero["semantic_test"]["expected_semantic_result"])
        self.assertEqual("CORE_BEHAVIOURAL", zero["score_stream"])

    def test_algorithm40_metadata_matches_empty_dequeue_fixture(self):
        suite = DEFAULT_COMMON_TESTS_ROOT / "Algorithm - 40" / "Algorithm 40 Tests.json"
        data = json.loads(suite.read_text(encoding="utf-8"))
        self.assertEqual("PARTIALLY_COVERED", data["coverage_dimensions"]["boundary_behaviour"])
        self.assertNotIn("not reached", " ".join(data.get("coverage_limitations", [])).lower())


if __name__ == "__main__":
    unittest.main()
