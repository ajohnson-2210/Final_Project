import unittest
from pathlib import Path
from unittest.mock import patch

from pseudocode_profiles import PseudocodeProfile
from pycharm_runner import ensure_baseline_available


class _DeclineDialog:
    def ask_yes_no(self, title, message):
        self.title = title
        self.message = message
        return False


class RunnerBaselineGuardV423Tests(unittest.TestCase):
    def test_declining_missing_baseline_cancels_dependent_operation_cleanly(self):
        dialog = _DeclineDialog()
        result = ensure_baseline_available(dialog, PseudocodeProfile.GENERIC_COMPATIBILITY)
        self.assertIsNone(result)
        self.assertIn("Baseline benchmark required", dialog.title)
        self.assertIn("provide one now", dialog.message)


class _PartialDialog:
    def __init__(self, baseline):
        self.baseline = Path(baseline)
        self.prompts = []
    def ask_yes_no(self, title, message):
        self.prompts.append((title, message))
        return True
    def select_optional_directory(self, title):
        return self.baseline
    def show_error(self, title, message):
        raise AssertionError(f"Unexpected error dialog: {title}: {message}")
    def show_info(self, title, message):
        self.prompts.append((title, message))


class RunnerPartialBaselineV425Tests(unittest.TestCase):
    def test_current_partial_baseline_does_not_force_recalibration_loop(self):
        dialog = _PartialDialog("/tmp/baseline")
        preflight = {"baseline_root_structure_valid": True, "issue_count": 0, "algorithms": []}
        state = {
            "terminal": 50,
            "evaluated": 32,
            "pipeline_failure": 17,
            "behavioural_not_evaluated": 1,
            "other_unavailable": 0,
        }
        with patch("pycharm_runner.validate_baseline", return_value=preflight), \
             patch("pycharm_runner._current_baseline_state", return_value=state), \
             patch("pycharm_runner.run_baseline_folder") as rerun:
            result = ensure_baseline_available(dialog, PseudocodeProfile.GENERIC_COMPATIBILITY)
        self.assertEqual(Path("/tmp/baseline"), result)
        rerun.assert_not_called()
        titles = [title for title, _ in dialog.prompts]
        self.assertIn("Baseline benchmark required", titles)
        self.assertIn("Baseline calibration has limitations", titles)


if __name__ == "__main__":
    unittest.main()
