import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, call

from input_selection import BaselineStartupAction, PostLLMAction
from pseudocode_profiles import PseudocodeProfile
from pycharm_runner import establish_session_baseline, run_llm_study_session


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


class _Dialog:
    def __init__(self):
        self.detected_action = BaselineStartupAction.USE_DETECTED_BASELINE
        self.optional_directory = None
        self.post_actions = []
        self.infos = []

    def select_detected_baseline_action(self, baseline_root, study_ready):
        self.detected = (Path(baseline_root), study_ready)
        return self.detected_action

    def select_optional_directory(self, title):
        self.optional_title = title
        return self.optional_directory

    def show_info(self, title, message):
        self.infos.append((title, message))

    def show_error(self, title, message):
        raise AssertionError(f"Unexpected error: {title}: {message}")

    def select_post_llm_action(self):
        return self.post_actions.pop(0)


class RunnerSessionFlowV435RC4Tests(unittest.TestCase):
    def test_detected_ready_baseline_requires_explicit_reuse_choice(self):
        with tempfile.TemporaryDirectory() as temp:
            baseline = Path(temp) / "Baselines"
            baseline.mkdir()
            dialog = _Dialog()
            with patch("pycharm_runner._saved_baseline_root", return_value=baseline), \
                 patch("pycharm_runner.validate_baseline", return_value=READY_PREFLIGHT), \
                 patch("pycharm_runner._current_baseline_state", return_value=READY_STATE), \
                 patch("pycharm_runner.ensure_baseline_available", return_value=baseline) as ensure:
                result = establish_session_baseline(dialog, PseudocodeProfile.GENERIC_COMPATIBILITY)

            self.assertEqual(baseline, result)
            self.assertEqual((baseline, True), dialog.detected)
            ensure.assert_called_once_with(
                dialog,
                PseudocodeProfile.GENERIC_COMPATIBILITY,
                baseline_root=baseline,
                require_full_study_readiness=True,
                persist_preference=True,
            )

    def test_detected_baseline_can_be_replaced_and_forced_recalibration(self):
        with tempfile.TemporaryDirectory() as temp:
            saved = Path(temp) / "Saved"
            selected = Path(temp) / "Selected"
            saved.mkdir()
            selected.mkdir()
            dialog = _Dialog()
            dialog.detected_action = BaselineStartupAction.CHOOSE_AND_RECALIBRATE
            dialog.optional_directory = selected
            with patch("pycharm_runner._saved_baseline_root", return_value=saved), \
                 patch("pycharm_runner.validate_baseline", return_value=READY_PREFLIGHT), \
                 patch("pycharm_runner._current_baseline_state", return_value=READY_STATE), \
                 patch("pycharm_runner.ensure_baseline_available", return_value=selected) as ensure:
                result = establish_session_baseline(dialog, PseudocodeProfile.GENERIC_COMPATIBILITY)

            self.assertEqual(selected, result)
            self.assertIn("recalibrate", dialog.optional_title.lower())
            ensure.assert_called_once_with(
                dialog,
                PseudocodeProfile.GENERIC_COMPATIBILITY,
                baseline_root=selected,
                require_full_study_readiness=True,
                persist_preference=True,
                force_recalibration=True,
            )

    def test_no_detected_baseline_directs_user_to_baseline_folder(self):
        with tempfile.TemporaryDirectory() as temp:
            selected = Path(temp) / "Baselines"
            selected.mkdir()
            dialog = _Dialog()
            dialog.optional_directory = selected
            with patch("pycharm_runner._saved_baseline_root", return_value=None), \
                 patch("pycharm_runner.ensure_baseline_available", return_value=selected) as ensure:
                result = establish_session_baseline(dialog, PseudocodeProfile.GENERIC_COMPATIBILITY)

            self.assertEqual(selected, result)
            self.assertTrue(any(title == "Baseline benchmark required" for title, _ in dialog.infos))
            ensure.assert_called_once_with(
                dialog,
                PseudocodeProfile.GENERIC_COMPATIBILITY,
                baseline_root=selected,
                require_full_study_readiness=True,
                persist_preference=True,
            )

    def test_another_llm_folder_reuses_same_session_baseline(self):
        with tempfile.TemporaryDirectory() as temp:
            baseline = Path(temp) / "Baselines"
            first = Path(temp) / "First Results"
            second = Path(temp) / "Second Results"
            baseline.mkdir(); first.mkdir(); second.mkdir()
            dialog = _Dialog()
            dialog.post_actions = [PostLLMAction.ANOTHER_LLM_RESULTS_FOLDER, PostLLMAction.QUIT]
            result = {"report": {"dataset": "x", "batch_type": "LLM_RESULTS"}, "json_path": "x", "csv_path": "y"}

            with patch("pycharm_runner.establish_session_baseline", return_value=baseline) as establish, \
                 patch("pycharm_runner.select_llm_results_directory", side_effect=[first, second]) as select_llm, \
                 patch("pycharm_runner._current_baseline_state", return_value=READY_STATE), \
                 patch("pycharm_runner._print_llm_run_header"), \
                 patch("pycharm_runner.run_selected_pipeline", return_value=result) as run_pipeline, \
                 patch("pycharm_runner._print_study_batch_result"):
                run_llm_study_session(dialog, PseudocodeProfile.GENERIC_COMPATIBILITY)

            establish.assert_called_once()
            self.assertEqual(2, select_llm.call_count)
            self.assertEqual(2, run_pipeline.call_count)
            self.assertEqual(
                [call(dialog, baseline), call(dialog, baseline)],
                select_llm.call_args_list,
            )

    def test_human_review_receives_all_llm_datasets_processed_in_session(self):
        with tempfile.TemporaryDirectory() as temp:
            baseline = Path(temp) / "Baselines"
            first = Path(temp) / "First Results"
            second = Path(temp) / "Second Results"
            baseline.mkdir(); first.mkdir(); second.mkdir()
            dialog = _Dialog()
            dialog.post_actions = [
                PostLLMAction.ANOTHER_LLM_RESULTS_FOLDER,
                PostLLMAction.HUMAN_EVALUATION,
                PostLLMAction.QUIT,
            ]
            result = {"report": {"dataset": "x", "batch_type": "LLM_RESULTS"}, "json_path": "x", "csv_path": "y"}

            with patch("pycharm_runner.establish_session_baseline", return_value=baseline), \
                 patch("pycharm_runner.select_llm_results_directory", side_effect=[first, second]), \
                 patch("pycharm_runner._current_baseline_state", return_value=READY_STATE), \
                 patch("pycharm_runner._print_llm_run_header"), \
                 patch("pycharm_runner.run_selected_pipeline", return_value=result), \
                 patch("pycharm_runner._print_study_batch_result"), \
                 patch("pycharm_runner.run_human_review_folder") as review:
                run_llm_study_session(dialog, PseudocodeProfile.GENERIC_COMPATIBILITY)

            review.assert_called_once()
            self.assertEqual([first, second], review.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
