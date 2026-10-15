from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "study components"
if str(STUDY) not in sys.path:
    sys.path.insert(0, str(STUDY))

from baseline_benchmark import validate_reference_python
from study_batch import StudyBatchProcessor
from pseudocode_profiles import PseudocodeProfile
from study_provenance import find_reference_python, validate_baseline


class BaselineReferenceDiscoveryV419Tests(unittest.TestCase):
    def _baseline_root(self, directory: str) -> tuple[Path, Path, Path]:
        root = Path(directory) / "Baselines"
        pseudo = root / "pseudocode" / "Algorithm - 1"
        python = root / "python" / "Algorithm - 1"
        pseudo.mkdir(parents=True)
        python.mkdir(parents=True)
        (pseudo / "Algorithm 1 Pseudocode.txt").write_text("OUTPUT STRING(\"ok\")\n", encoding="utf-8")
        return root, pseudo, python

    def test_accepts_frozen_baseline_python_txt_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, python = self._baseline_root(directory)
            ref = python / "Algorithm 1 Baseline Python code.txt"
            ref.write_text("print('ok')\n", encoding="utf-8")

            self.assertEqual(find_reference_python(python, 1), ref)
            report = validate_baseline(root, expected_ids=[1], common_tests_root=Path(directory) / "no_common_tests")
            row = report["algorithms"][0]
            self.assertEqual(Path(row["reference_python"]), ref.resolve())
            self.assertNotIn("REFERENCE_PYTHON_MISSING_OR_AMBIGUOUS", row["issues"])
            self.assertIn("TESTS_MISSING", row["issues"])

    def test_accepts_frozen_baseline_python_py_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, python = self._baseline_root(directory)
            ref = python / "Algorithm 1 Baseline Python code.py"
            ref.write_text("print('ok')\n", encoding="utf-8")

            self.assertEqual(find_reference_python(python, 1), ref)
            report = validate_baseline(root, expected_ids=[1], common_tests_root=Path(directory) / "no_common_tests")
            self.assertEqual(Path(report["algorithms"][0]["reference_python"]), ref.resolve())

    def test_recognised_reference_names_are_ambiguous_if_multiple_exist(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, python = self._baseline_root(directory)
            (python / "Algorithm 1 Baseline Python code.py").write_text("print('py')\n", encoding="utf-8")
            (python / "Algorithm 1 Baseline Python code.txt").write_text("print('txt')\n", encoding="utf-8")

            self.assertIsNone(find_reference_python(python, 1))
            report = validate_baseline(root, expected_ids=[1], common_tests_root=Path(directory) / "no_common_tests")
            self.assertIn("REFERENCE_PYTHON_MISSING_OR_AMBIGUOUS", report["algorithms"][0]["issues"])

    def test_txt_reference_executes_as_python_source(self):
        with tempfile.TemporaryDirectory() as directory:
            _, _, python = self._baseline_root(directory)
            ref = python / "Algorithm 1 Baseline Python code.txt"
            ref.write_text("print('ok')\n", encoding="utf-8")
            validation = validate_reference_python(ref, [{"name": "output", "expected_output": ["ok"]}])
            self.assertEqual(validation["status"], "VALIDATED")

    def test_legacy_single_py_fallback_remains_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            _, _, python = self._baseline_root(directory)
            ref = python / "reference_impl.py"
            ref.write_text("print('ok')\n", encoding="utf-8")
            self.assertEqual(find_reference_python(python, 1), ref)

    def test_end_to_end_baseline_calibration_uses_txt_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            root, pseudo, python = self._baseline_root(directory)
            ref = python / "Algorithm 1 Baseline Python code.txt"
            ref.write_text("print('ok')\n", encoding="utf-8")
            (python / "Algorithm 1 Tests.json").write_text(
                '{"tests":[{"name":"output","expected_output":["ok"]}]}',
                encoding="utf-8",
            )

            result = StudyBatchProcessor(common_tests_root=Path(directory) / "no_common_tests").process_baseline(
                root, profile=PseudocodeProfile.AJ_DIALECT_STRICT
            )
            record = result["report"]["algorithms"][0]
            self.assertEqual(record["reference_python"], str(ref.resolve()))
            self.assertEqual(record["reference_validation_status"], "VALIDATED")
            self.assertEqual(record["calibration_status"], "CALIBRATED")
            self.assertEqual(result["report"]["pipeline_status_counts"], {"SUCCESS": 1})
            self.assertEqual(result["report"]["calibration_status_counts"], {"CALIBRATED": 1})
            self.assertTrue((pseudo / "pipeline_artifacts" / "baseline_reference_validation.json").exists())


if __name__ == "__main__":
    unittest.main()
