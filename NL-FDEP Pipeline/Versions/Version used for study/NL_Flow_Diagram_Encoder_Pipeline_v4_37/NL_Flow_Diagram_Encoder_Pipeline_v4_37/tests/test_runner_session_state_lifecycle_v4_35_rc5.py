import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from input_selection import InputRoute, InputSelectionCancelledError
from pseudocode_profiles import PseudocodeProfile
import pycharm_runner


READY_STATE = {
    "terminal": 50,
    "evaluated": 49,
    "full_score": 49,
    "pipeline_failure": 0,
    "behavioural_not_evaluated": 1,
    "other_unavailable": 0,
}


class _Dialog:
    def __init__(self, routes=None, selected_file=None, cancel=False):
        self.routes = list(routes or [])
        self.selected_file = selected_file
        self.cancel = cancel

    def select_route(self):
        if self.cancel:
            raise InputSelectionCancelledError("Input selection cancelled.")
        if not self.routes:
            raise InputSelectionCancelledError("Input type selection was cancelled.")
        return self.routes.pop(0)

    def select_pseudocode_profile(self):
        return PseudocodeProfile.GENERIC_COMPATIBILITY

    def select_file(self, route):
        return self.selected_file

    def show_error(self, title, message):
        raise AssertionError(f"Unexpected error: {title}: {message}")


class RunnerSessionStateLifecycleV435RC5Tests(unittest.TestCase):
    def test_orderly_llm_session_exit_clears_recovery_hint(self):
        dialog = _Dialog(routes=[InputRoute.LLM_RESULTS_FOLDER])
        with patch("pycharm_runner.InputSelectionDialog", return_value=dialog), \
             patch("pycharm_runner.ensure_runner_dependencies", return_value=True), \
             patch("pycharm_runner.run_llm_study_session") as run_session, \
             patch("pycharm_runner._clear_baseline_preference") as clear_hint:
            pycharm_runner.main()

        run_session.assert_called_once_with(
            dialog,
            PseudocodeProfile.GENERIC_COMPATIBILITY,
            selected_baseline_root=None,
            session_llm_results=[],
        )
        clear_hint.assert_called_once_with()

    def test_cancelled_runner_exit_clears_recovery_hint(self):
        dialog = _Dialog(cancel=True)
        with patch("pycharm_runner.InputSelectionDialog", return_value=dialog), \
             patch("pycharm_runner._clear_baseline_preference") as clear_hint:
            pycharm_runner.main()

        clear_hint.assert_called_once_with()

    def test_baseline_route_returns_to_menu_and_is_reused_by_llm_in_same_process(self):
        baseline = Path("Baselines")
        dialog = _Dialog(
            routes=[InputRoute.BASELINE_BENCHMARK_FOLDER, InputRoute.LLM_RESULTS_FOLDER],
            selected_file=baseline,
        )
        result = {"report": {"batch_type": "BASELINE"}}
        pack = Mock(complete=True, suite_count=50, test_count=156)

        with patch("pycharm_runner.InputSelectionDialog", return_value=dialog), \
             patch("pycharm_runner.ensure_runner_dependencies", return_value=True), \
             patch("pycharm_runner.validate_common_test_pack", return_value=pack), \
             patch("pycharm_runner.validate_baseline", return_value={
                 "baseline_root_structure_valid": True,
                 "issue_count": 0,
                 "baseline_design_status": "MATCH",
                 "baseline_algorithm_count": 50,
                 "baseline_design": {"status": "MATCH", "baseline_algorithm_count": 50},
                 "algorithms": [],
             }), \
             patch("pycharm_runner.run_selected_pipeline", return_value=result), \
             patch("pycharm_runner._print_study_batch_result"), \
             patch("pycharm_runner._current_baseline_state", return_value=READY_STATE), \
             patch("pycharm_runner._save_baseline_preference") as save_hint, \
             patch("pycharm_runner.run_llm_study_session") as run_session, \
             patch("pycharm_runner._clear_baseline_preference") as clear_hint:
            pycharm_runner.main()

        save_hint.assert_called_once_with(baseline)
        run_session.assert_called_once_with(
            dialog,
            PseudocodeProfile.GENERIC_COMPATIBILITY,
            selected_baseline_root=baseline,
            session_llm_results=[],
        )
        clear_hint.assert_called_once_with()

    def test_unexpected_llm_exception_preserves_recovery_hint(self):
        dialog = _Dialog(routes=[InputRoute.LLM_RESULTS_FOLDER])
        with patch("pycharm_runner.InputSelectionDialog", return_value=dialog), \
             patch("pycharm_runner.ensure_runner_dependencies", return_value=True), \
             patch("pycharm_runner.run_llm_study_session", side_effect=RuntimeError("boom")), \
             patch("pycharm_runner._clear_baseline_preference") as clear_hint:
            with self.assertRaisesRegex(RuntimeError, "boom"):
                pycharm_runner.main()

        clear_hint.assert_not_called()


if __name__ == "__main__":
    unittest.main()
