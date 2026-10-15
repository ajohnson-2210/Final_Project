import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from input_selection import HumanReviewStartupAction, InputRoute
from pycharm_runner import _run_main_menu
from study_review import previous_study_review_roots, remember_review_study


class HumanReviewRC14Tests(unittest.TestCase):
    def _write_questionnaire(self, root: Path, aid: int, dataset: str, *, is_baseline: bool = False):
        scoring = root / f"Algorithm - {aid}" / "pipeline_artifacts" / "scoring"
        scoring.mkdir(parents=True, exist_ok=True)
        payload = {
            "algorithm": {"algorithm_id": aid, "dataset": dataset, "is_baseline": is_baseline},
            "criteria": [],
        }
        (scoring / "human_review_questionnaire.json").write_text(json.dumps(payload), encoding="utf-8")
        return scoring

    def test_persisted_study_rebuilds_all_experimental_siblings_and_excludes_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            study = base / "Study"
            a_results = study / "Agent A" / "Results"
            b_results = study / "Agent B" / "Results"
            baseline_results = study / "Baselines" / "Results"
            self._write_questionnaire(a_results, 1, "Agent A")
            self._write_questionnaire(b_results, 1, "Agent B")
            self._write_questionnaire(baseline_results, 1, "Baseline", is_baseline=True)
            state_file = base / "human_review_state.json"

            with patch.dict(os.environ, {"NL_FDEP_HUMAN_REVIEW_STATE_FILE": str(state_file)}):
                remembered = remember_review_study(study / "Agent B")
                self.assertEqual(study.resolve(), remembered)
                roots = previous_study_review_roots()

            self.assertEqual([a_results.resolve(), b_results.resolve()], roots)

    def test_detect_previous_study_opens_review_without_folder_chooser(self):
        class Dialog:
            def select_route(self):
                return InputRoute.HUMAN_REVIEW_FOLDER

            def select_human_review_startup_action(self):
                return HumanReviewStartupAction.RESUME_DISCOVER_EXISTING_STUDY

            def select_file(self, route):
                raise AssertionError("folder chooser must not be called when previous study is detected")

            def show_info(self, title, message):
                raise AssertionError("fallback info should not be shown when previous study exists")

        roots = [Path("C:/Study/Agent A/Results"), Path("C:/Study/Agent B/Results")]
        with patch("pycharm_runner.previous_study_review_roots", return_value=roots), patch(
            "pycharm_runner.run_human_review_folder", return_value={"status": "REVIEW_SESSION_CLOSED"}
        ) as launch:
            _run_main_menu(Dialog())

        launch.assert_called_once_with(roots, discover_siblings=False, regenerate_dashboards=True)


if __name__ == "__main__":
    unittest.main()
