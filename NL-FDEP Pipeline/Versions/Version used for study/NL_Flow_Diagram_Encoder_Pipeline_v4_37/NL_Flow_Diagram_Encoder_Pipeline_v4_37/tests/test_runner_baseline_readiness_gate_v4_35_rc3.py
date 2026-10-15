import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from input_selection import InputRoute
from pseudocode_profiles import PseudocodeProfile
from pycharm_runner import (
    _baseline_study_ready,
    ensure_baseline_available,
    run_selected_pipeline,
)


READY_PREFLIGHT = {
    "baseline_root_structure_valid": True,
    "issue_count": 0,
    "algorithms": [],
}
READY_STATE = {
    "terminal": 50,
    "evaluated": 50,
    "full_score": 50,
    "pipeline_failure": 0,
    "behavioural_not_evaluated": 0,
    "other_unavailable": 0,
}
PARTIAL_STATE = {
    "terminal": 50,
    "evaluated": 50,
    "full_score": 49,
    "pipeline_failure": 0,
    "behavioural_not_evaluated": 0,
    "other_unavailable": 0,
}


class _GateDialog:
    def __init__(self, baseline: Path, answers=None):
        self.baseline = Path(baseline)
        self.answers = list(answers or [])
        self.questions = []
        self.errors = []
        self.infos = []

    def ask_yes_no(self, title, message):
        self.questions.append((title, message))
        if not self.answers:
            raise AssertionError(f"Unexpected question: {title}: {message}")
        return self.answers.pop(0)

    def select_optional_directory(self, title):
        return self.baseline

    def show_error(self, title, message):
        self.errors.append((title, message))

    def show_info(self, title, message):
        self.infos.append((title, message))


class RunnerBaselineReadinessGateV435RC3Tests(unittest.TestCase):
    def test_ready_requires_all_pipeline_success_and_all_evaluable_at_100_percent(self):
        self.assertTrue(_baseline_study_ready(READY_STATE))
        self.assertFalse(_baseline_study_ready(PARTIAL_STATE))
        self.assertTrue(_baseline_study_ready({
            **READY_STATE,
            "evaluated": 49,
            "full_score": 49,
            "behavioural_not_evaluated": 1,
        }))
        self.assertFalse(_baseline_study_ready({**READY_STATE, "terminal": 49}))
        self.assertFalse(_baseline_study_ready({**READY_STATE, "pipeline_failure": 1}))

    def test_missing_baseline_is_selected_calibrated_and_then_allows_llm_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            baseline = Path(temp) / "Baselines"
            baseline.mkdir()
            dialog = _GateDialog(baseline, answers=[True, True])
            calibration_result = {
                "report": {
                    "algorithm_count": 50,
                    "calibration_status_counts": {"CALIBRATED": 50},
                }
            }
            with patch("pycharm_runner.validate_baseline", return_value=READY_PREFLIGHT), \
                 patch("pycharm_runner._current_baseline_state", side_effect=[{**READY_STATE, "terminal": 0, "evaluated": 0, "full_score": 0}, READY_STATE]), \
                 patch("pycharm_runner.run_baseline_folder", return_value=calibration_result) as calibrate, \
                 patch("pycharm_runner._save_baseline_preference") as save:
                result = ensure_baseline_available(
                    dialog,
                    PseudocodeProfile.GENERIC_COMPATIBILITY,
                    require_full_study_readiness=True,
                )

            self.assertEqual(baseline, result)
            calibrate.assert_called_once()
            save.assert_called_once_with(baseline)
            self.assertEqual([], dialog.errors)
            self.assertEqual(
                ["Baseline benchmark required", "Baseline calibration required"],
                [title for title, _ in dialog.questions],
            )

    def test_incomplete_or_below_100_calibration_blocks_llm_operation(self):
        with tempfile.TemporaryDirectory() as temp:
            baseline = Path(temp) / "Baselines"
            baseline.mkdir()
            dialog = _GateDialog(baseline, answers=[True])
            calibration_result = {
                "report": {
                    "algorithm_count": 50,
                    "calibration_status_counts": {"CALIBRATED": 50},
                }
            }
            with patch("pycharm_runner.validate_baseline", return_value=READY_PREFLIGHT), \
                 patch("pycharm_runner._current_baseline_state", side_effect=[PARTIAL_STATE, PARTIAL_STATE]), \
                 patch("pycharm_runner.run_baseline_folder", return_value=calibration_result), \
                 patch("pycharm_runner._save_baseline_preference") as save:
                result = ensure_baseline_available(
                    dialog,
                    PseudocodeProfile.GENERIC_COMPATIBILITY,
                    baseline_root=baseline,
                    require_full_study_readiness=True,
                )

            self.assertIsNone(result)
            save.assert_not_called()
            self.assertTrue(any(title == "Baseline calibration is not study-ready" for title, _ in dialog.errors))

    def test_llm_pipeline_does_not_receive_gate_baseline_path(self):
        with tempfile.TemporaryDirectory() as temp:
            results = Path(temp) / "Results"
            baseline = Path(temp) / "Baselines"
            results.mkdir()
            baseline.mkdir()
            sentinel = {"ok": True}
            with patch("pycharm_runner.run_llm_results_folder", return_value=sentinel) as run_llm:
                result = run_selected_pipeline(
                    InputRoute.LLM_RESULTS_FOLDER,
                    results,
                    PseudocodeProfile.GENERIC_COMPATIBILITY,
                    baseline_root=baseline,
                )

            self.assertIs(sentinel, result)
            run_llm.assert_called_once_with(
                input_path=results,
                pseudocode_profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
            )


if __name__ == "__main__":
    unittest.main()
