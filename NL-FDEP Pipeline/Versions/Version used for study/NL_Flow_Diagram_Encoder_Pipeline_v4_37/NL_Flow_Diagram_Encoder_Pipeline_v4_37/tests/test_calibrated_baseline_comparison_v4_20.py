from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "study components"
if str(STUDY) not in sys.path:
    sys.path.insert(0, str(STUDY))

from pseudocode_profiles import PseudocodeProfile
from study_batch import StudyBatchProcessor


class CalibratedBaselineComparisonV420Tests(unittest.TestCase):
    def _baseline(self, directory: str, baseline_pseudocode: str = 'OUTPUT STRING("ok")\n') -> Path:
        root = Path(directory) / "Baseline"
        pseudo = root / "pseudocode" / "Algorithm - 1"
        python = root / "python" / "Algorithm - 1"
        pseudo.mkdir(parents=True)
        python.mkdir(parents=True)
        (pseudo / "Algorithm 1 Pseudocode.txt").write_text(baseline_pseudocode, encoding="utf-8")
        (python / "Algorithm 1 Baseline Python code.txt").write_text("print('ok')\n", encoding="utf-8")
        (python / "Algorithm 1 Tests.json").write_text(
            json.dumps({"tests": [{"name": "common-output"}]}), encoding="utf-8"
        )
        return root

    def test_input_only_tests_create_trusted_reference_calibration(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = self._baseline(directory)
            result = StudyBatchProcessor(common_tests_root=Path(directory)/"no_pack").process_baseline(
                baseline, profile=PseudocodeProfile.AJ_DIALECT_STRICT
            )
            record = result["report"]["algorithms"][0]
            self.assertEqual("TRUSTED_REFERENCE", record["reference_validation_status"])
            self.assertEqual("CALIBRATED", record["calibration_status"])
            self.assertEqual(100.0, record["baseline_calibration_percentage"])

    def test_experimental_result_uses_frozen_pack_not_supplied_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = self._baseline(directory)
            results = Path(directory) / "source_a" / "results"
            algorithm = results / "Algorithm - 1"
            algorithm.mkdir(parents=True)
            (algorithm / "Algorithm 1 Pseudocode.txt").write_text(
                "FUNCTION f ACCEPTS(a, b)\n    RETURN BOOLEAN(FALSE)\nENDFUNCTION\n", encoding="utf-8"
            )
            result = StudyBatchProcessor().process_llm_results(
                results, profile=PseudocodeProfile.AJ_DIALECT_STRICT, baseline_root=baseline
            )
            record = result["report"]["algorithms"][0]
            self.assertEqual(100.0, record["experimental_behavioural_percentage"])
            self.assertEqual("AT_REFERENCE", record["comparison_to_baseline"])
            comparison = json.loads((algorithm/"pipeline_artifacts"/"baseline_relative_comparison.json").read_text())
            self.assertFalse(comparison["runtime_baseline_reference_used"])
            self.assertTrue(comparison["baseline_root_supplied_but_not_used"])
            self.assertIsNone(comparison["reference_python"])
            self.assertEqual("STATIC_PREEXPERIMENT_EXPECTATIONS", comparison["expected_value_policy"])

    def test_calibration_score_is_measured_even_when_below_100(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = self._baseline(directory, baseline_pseudocode='OUTPUT STRING("wrong")\n')
            result = StudyBatchProcessor(common_tests_root=Path(directory)/"no_pack").process_baseline(
                baseline, profile=PseudocodeProfile.AJ_DIALECT_STRICT
            )
            record = result["report"]["algorithms"][0]
            self.assertEqual("FAILURE", record["status"])
            self.assertEqual("CALIBRATED", record["calibration_status"])
            self.assertEqual(0.0, record["baseline_calibration_percentage"])

    def test_experimental_resume_does_not_depend_on_baseline_calibration_run_id(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = self._baseline(directory)
            processor = StudyBatchProcessor()
            results = Path(directory) / "source_a" / "results"
            algorithm = results / "Algorithm - 1"
            algorithm.mkdir(parents=True)
            (algorithm / "Algorithm 1 Pseudocode.txt").write_text(
                "FUNCTION f ACCEPTS(a, b)\n    RETURN BOOLEAN(FALSE)\nENDFUNCTION\n", encoding="utf-8"
            )
            first = processor.process_llm_results(results, profile=PseudocodeProfile.AJ_DIALECT_STRICT, baseline_root=baseline)
            self.assertEqual("PROCESSED", first["report"]["algorithms"][0]["action"])
            second = processor.process_llm_results(results, profile=PseudocodeProfile.AJ_DIALECT_STRICT, baseline_root=None)
            self.assertEqual("SKIPPED_CURRENT", second["report"]["algorithms"][0]["action"])

    def test_unvalidated_baseline_cannot_become_experimental_oracle(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = self._baseline(directory)
            # Deliberately wrong reference: experimental scoring must ignore it.
            ref = baseline / "python" / "Algorithm - 1" / "Algorithm 1 Baseline Python code.txt"
            ref.write_text("print('WRONG_ORACLE')\n", encoding="utf-8")
            results = Path(directory) / "source_a" / "results"
            algorithm = results / "Algorithm - 1"
            algorithm.mkdir(parents=True)
            (algorithm / "Algorithm 1 Pseudocode.txt").write_text(
                "FUNCTION f ACCEPTS(a, b)\n    RETURN BOOLEAN(FALSE)\nENDFUNCTION\n", encoding="utf-8"
            )
            StudyBatchProcessor().process_llm_results(results, profile=PseudocodeProfile.AJ_DIALECT_STRICT, baseline_root=baseline)
            comparison = json.loads((algorithm/"pipeline_artifacts"/"baseline_relative_comparison.json").read_text())
            self.assertFalse(comparison["runtime_baseline_reference_used"])
            self.assertEqual(100.0, comparison["experimental_behavioural_score_percentage"])
            self.assertEqual("AT_REFERENCE", comparison["comparison_to_frozen_reference"])


if __name__ == "__main__":
    unittest.main()
