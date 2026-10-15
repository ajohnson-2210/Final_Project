from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pycharm_runner import _baseline_study_ready, _current_baseline_state
from study_provenance import baseline_algorithm_design, validate_baseline


def _write_baseline_algorithm(root: Path, aid: int, *, pseudo: bool = True, python: bool = True) -> None:
    if pseudo:
        pdir = root / "pseudocode" / f"Algorithm - {aid}"
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / f"Algorithm {aid} Pseudocode.txt").write_text('OUTPUT STRING("ok")\n', encoding="utf-8")
    if python:
        ydir = root / "python" / f"Algorithm - {aid}"
        ydir.mkdir(parents=True, exist_ok=True)
        (ydir / f"Algorithm {aid} Baseline Python code.py").write_text("print('ok')\n", encoding="utf-8")
        (ydir / f"Algorithm {aid} Tests.json").write_text(
            '{"tests":[{"name":"output","expected_output":["ok"]}]}',
            encoding="utf-8",
        )


def _write_ready_artifacts(root: Path, aid: int, *, evaluated: bool = True) -> None:
    art = root / "pseudocode" / f"Algorithm - {aid}" / "pipeline_artifacts"
    art.mkdir(parents=True, exist_ok=True)
    (art / "manifest.json").write_text(
        json.dumps({
            "pipeline_version": "4.37",
            "pseudocode_profile": "AJ_DIALECT_STRICT",
            "processing_status": "SUCCESS",
        }),
        encoding="utf-8",
    )
    calibration = {
        "status": "EVALUATED" if evaluated else "NOT_EVALUATED",
        "calibration_score_percentage": 100.0 if evaluated else None,
    }
    (art / "baseline_calibration.json").write_text(json.dumps(calibration), encoding="utf-8")


class DynamicBaselineAlgorithmCountV437Tests(unittest.TestCase):
    def test_valid_baseline_establishes_independent_b_from_submitted_count(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "Baseline"
            for aid in range(1, 4):
                _write_baseline_algorithm(root, aid)

            design = baseline_algorithm_design(root)
            self.assertEqual(3, design["baseline_algorithm_count"])
            self.assertEqual([1, 2, 3], design["expected_algorithm_ids"])
            self.assertEqual("MATCH", design["status"])

            report = validate_baseline(root, common_tests_root=Path(td) / "no_common_tests")
            self.assertEqual(3, report["baseline_algorithm_count"])
            self.assertEqual([1, 2, 3], report["baseline_expected_algorithm_ids"])
            self.assertEqual("MATCH", report["baseline_design_status"])
            self.assertEqual(0, report["issue_count"])

    def test_same_count_with_non_contiguous_ids_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "Baseline"
            for aid in (1, 2, 4):
                _write_baseline_algorithm(root, aid)

            design = baseline_algorithm_design(root)
            self.assertEqual(3, design["baseline_algorithm_count"])
            self.assertEqual([1, 2, 3], design["expected_algorithm_ids"])
            self.assertEqual([3], design["missing_pseudocode_algorithm_ids"])
            self.assertEqual([3], design["missing_python_algorithm_ids"])
            self.assertEqual([4], design["extra_pseudocode_algorithm_ids"])
            self.assertEqual([4], design["extra_python_algorithm_ids"])
            self.assertEqual("MISMATCH", design["status"])

            report = validate_baseline(root, common_tests_root=Path(td) / "no_common_tests")
            self.assertGreater(report["issue_count"], 0)
            self.assertEqual("MISMATCH", report["baseline_design_status"])

    def test_pseudocode_python_count_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "Baseline"
            for aid in range(1, 4):
                _write_baseline_algorithm(root, aid)
            _write_baseline_algorithm(root, 4, pseudo=True, python=False)

            design = baseline_algorithm_design(root)
            self.assertEqual(4, design["baseline_algorithm_count"])
            self.assertEqual([4], design["missing_python_algorithm_ids"])
            self.assertIn("BASELINE_PSEUDOCODE_PYTHON_ID_SET_MISMATCH", design["issues"])
            self.assertEqual("MISMATCH", design["status"])

    def test_readiness_uses_b_not_fifty(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "Baseline"
            for aid in range(1, 4):
                _write_baseline_algorithm(root, aid)
                _write_ready_artifacts(root, aid)

            state = _current_baseline_state(root)
            self.assertEqual(3, state["required_count"])
            self.assertEqual(3, state["terminal"])
            self.assertEqual(3, state["evaluated"])
            self.assertTrue(_baseline_study_ready(state))

    def test_existing_one_not_evaluated_rule_scales_with_b(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "Baseline"
            for aid in range(1, 4):
                _write_baseline_algorithm(root, aid)
                _write_ready_artifacts(root, aid, evaluated=(aid != 3))

            state = _current_baseline_state(root)
            self.assertEqual(3, state["required_count"])
            self.assertEqual(2, state["evaluated"])
            self.assertEqual(1, state["behavioural_not_evaluated"])
            self.assertTrue(_baseline_study_ready(state))


if __name__ == "__main__":
    unittest.main()
