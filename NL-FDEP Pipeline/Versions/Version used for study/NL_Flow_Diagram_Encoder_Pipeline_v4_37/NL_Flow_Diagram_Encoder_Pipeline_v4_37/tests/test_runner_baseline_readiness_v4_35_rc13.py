import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pseudocode_profiles import PseudocodeProfile
from pycharm_runner import _baseline_session_ready, _baseline_study_ready, ensure_baseline_available


READY_PREFLIGHT = {
    "baseline_root_structure_valid": True,
    "issue_count": 0,
    "algorithms": [],
}

READY_49_EVALUABLE_STATE = {
    "terminal": 50,
    "evaluated": 49,
    "full_score": 49,
    "pipeline_failure": 0,
    "behavioural_not_evaluated": 1,
    "other_unavailable": 0,
}

DEPENDENCY_FAILURE_STATE = {
    "terminal": 50,
    "evaluated": 49,
    "full_score": 49,
    "pipeline_failure": 1,
    "behavioural_not_evaluated": 0,
    "other_unavailable": 0,
}

BELOW_100_STATE = {
    "terminal": 50,
    "evaluated": 50,
    "full_score": 49,
    "pipeline_failure": 0,
    "behavioural_not_evaluated": 0,
    "other_unavailable": 0,
}

MATPLOTLIB_PROBLEM = {
    "algorithm_id": 50,
    "category": "PIPELINE_FAILURE",
    "reason": "ModuleNotFoundError: No module named 'matplotlib'",
    "processing_status": "FAILURE",
    "calibration_status": "PIPELINE_FAILURE",
    "calibration_score_percentage": None,
}


class _Dialog:
    def __init__(self, answers):
        self.answers = list(answers)
        self.questions = []
        self.errors = []

    def ask_yes_no(self, title, message):
        self.questions.append((title, message))
        if not self.answers:
            raise AssertionError(f"Unexpected question: {title}: {message}")
        return self.answers.pop(0)

    def show_error(self, title, message):
        self.errors.append((title, message))

    def show_info(self, title, message):
        pass

    def select_optional_directory(self, title):
        raise AssertionError("Directory selection was not expected in this test")


class RunnerBaselineReadinessV435RC13Tests(unittest.TestCase):
    def test_49_evaluable_plus_one_genuine_not_evaluated_is_full_readiness(self):
        self.assertTrue(_baseline_study_ready(READY_49_EVALUABLE_STATE))
        self.assertTrue(_baseline_session_ready(Path("Baselines"), READY_49_EVALUABLE_STATE))

    def test_pipeline_failure_never_uses_a_degraded_override(self):
        self.assertFalse(_baseline_study_ready(DEPENDENCY_FAILURE_STATE))
        self.assertFalse(_baseline_session_ready(Path("Baselines"), DEPENDENCY_FAILURE_STATE))

    def test_below_100_evaluable_calibration_is_not_ready(self):
        self.assertFalse(_baseline_study_ready(BELOW_100_STATE))

    def test_dependency_failure_blocks_after_calibration_without_49_override_prompt(self):
        with tempfile.TemporaryDirectory() as temp:
            baseline = Path(temp) / "Baselines"
            baseline.mkdir()
            dialog = _Dialog([True])
            calibration_result = {
                "report": {
                    "algorithm_count": 50,
                    "calibration_status_counts": {"CALIBRATED": 49, "PIPELINE_FAILURE": 1},
                    "algorithms": [],
                }
            }
            with patch("pycharm_runner.validate_baseline", return_value=READY_PREFLIGHT), \
                 patch("pycharm_runner._current_baseline_state", side_effect=[DEPENDENCY_FAILURE_STATE, DEPENDENCY_FAILURE_STATE]), \
                 patch("pycharm_runner.run_baseline_folder", return_value=calibration_result), \
                 patch("pycharm_runner._baseline_calibration_problem_details", return_value=[MATPLOTLIB_PROBLEM]), \
                 patch("pycharm_runner._save_baseline_preference") as save:
                result = ensure_baseline_available(
                    dialog,
                    PseudocodeProfile.GENERIC_COMPATIBILITY,
                    baseline_root=baseline,
                    require_full_study_readiness=True,
                )

            self.assertIsNone(result)
            save.assert_not_called()
            self.assertEqual(1, len(dialog.questions))
            self.assertNotIn("49/50", dialog.questions[0][0])
            self.assertTrue(any(title == "Baseline calibration is not study-ready" for title, _ in dialog.errors))
            self.assertIn("matplotlib", dialog.errors[0][1])


if __name__ == "__main__":
    unittest.main()
