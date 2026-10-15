import json
import tempfile
import unittest
from pathlib import Path

from pseudocode_profiles import PseudocodeProfile
from pycharm_runner import (
    BASELINE_CALIBRATION_PROFILE,
    _current_baseline_calibration_count,
    _current_baseline_state,
)
from study_batch import _baseline_calibration_status, _load_baseline_calibration_context
from study_provenance import manifest_is_current, sha256_file


class BaselineCalibrationStateV426Tests(unittest.TestCase):
    def test_controlled_baseline_profile_is_strict(self):
        self.assertEqual(PseudocodeProfile.AJ_DIALECT_STRICT, BASELINE_CALIBRATION_PROFILE)

    def test_measured_zero_percent_calibration_remains_calibrated(self):
        validation = {"status": "VALIDATED"}
        benchmark = {"status": "EVALUATED", "calibration_score_percentage": 0.0}
        self.assertEqual(
            "CALIBRATED",
            _baseline_calibration_status("FAILURE", validation, benchmark),
        )

    def test_generic_profile_calibration_is_not_current_or_experiment_eligible(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            art = root / "pseudocode" / "Algorithm - 1" / "pipeline_artifacts"
            art.mkdir(parents=True)
            (art / "manifest.json").write_text(json.dumps({
                "pipeline_version": "4.37",
                "pseudocode_profile": "GENERIC_COMPATIBILITY",
                "processing_status": "SUCCESS",
                "run_id": "generic-run",
            }))
            (art / "baseline_calibration.json").write_text(json.dumps({
                "status": "EVALUATED",
                "calibration_score_percentage": 100.0,
            }))
            (art / "baseline_reference_validation.json").write_text(json.dumps({"status": "VALIDATED"}))
            self.assertEqual(0, _current_baseline_calibration_count(root, expected_ids=[1]))
            context = _load_baseline_calibration_context(root, 1)
            self.assertFalse(context["current"])

    def test_evaluated_calibration_is_current_even_when_pipeline_status_records_test_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            art = root / "pseudocode" / "Algorithm - 1" / "pipeline_artifacts"
            art.mkdir(parents=True)
            (art / "manifest.json").write_text(json.dumps({
                "pipeline_version": "4.37",
                "pseudocode_profile": "AJ_DIALECT_STRICT",
                "processing_status": "FAILURE",
                "run_id": "measured-run",
            }))
            (art / "baseline_calibration.json").write_text(json.dumps({
                "status": "EVALUATED",
                "calibration_score_percentage": 0.0,
            }))
            (art / "baseline_reference_validation.json").write_text(json.dumps({"status": "TRUSTED_REFERENCE"}))
            self.assertEqual(1, _current_baseline_calibration_count(root, expected_ids=[1]))
            context = _load_baseline_calibration_context(root, 1)
            self.assertTrue(context["current"])
            self.assertEqual(0.0, context["calibration"]["calibration_score_percentage"])

    def test_baseline_state_separates_measured_disagreement_from_unavailable_runs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cases = {
                1: ("FAILURE", {"status": "EVALUATED", "calibration_score_percentage": 0.0}),
                2: ("FAILURE", {"status": "NOT_EVALUATED", "calibration_score_percentage": None}),
                3: ("SUCCESS", {"status": "NOT_EVALUATED", "calibration_score_percentage": None}),
            }
            for algorithm_id, (status, calibration) in cases.items():
                art = root / "pseudocode" / f"Algorithm - {algorithm_id}" / "pipeline_artifacts"
                art.mkdir(parents=True)
                (art / "manifest.json").write_text(json.dumps({
                    "pipeline_version": "4.37",
                    "pseudocode_profile": "AJ_DIALECT_STRICT",
                    "processing_status": status,
                    "run_id": f"run-{algorithm_id}",
                }))
                (art / "baseline_calibration.json").write_text(json.dumps(calibration))
            state = _current_baseline_state(root, expected_ids=[1, 2, 3])
            self.assertEqual(3, state["terminal"])
            self.assertEqual(1, state["evaluated"])
            self.assertEqual(1, state["pipeline_failure"])
            self.assertEqual(1, state["behavioural_not_evaluated"])

    def test_manifest_currentness_includes_profile(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.txt"
            ref = root / "ref.py"
            tests = root / "tests.json"
            source.write_text("OUTPUT 1\n")
            ref.write_text("print(1)\n")
            tests.write_text("{}")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "pipeline_version": "4.37",
                "rubric_version": "1.1",
                "rubric_sha256": "rubric",
                "pseudocode_profile": "AJ_DIALECT_STRICT",
                "source_pseudocode_sha256": sha256_file(source),
                "reference_python_sha256": sha256_file(ref),
                "tests_sha256": sha256_file(tests),
            }))
            self.assertFalse(manifest_is_current(
                manifest,
                source_file=source,
                pipeline_version="4.37",
                rubric_version="1.1",
                rubric_sha256="rubric",
                reference_python=ref,
                tests_file=tests,
                pseudocode_profile="GENERIC_COMPATIBILITY",
            ))
            self.assertTrue(manifest_is_current(
                manifest,
                source_file=source,
                pipeline_version="4.37",
                rubric_version="1.1",
                rubric_sha256="rubric",
                reference_python=ref,
                tests_file=tests,
                pseudocode_profile="AJ_DIALECT_STRICT",
            ))


if __name__ == "__main__":
    unittest.main()
