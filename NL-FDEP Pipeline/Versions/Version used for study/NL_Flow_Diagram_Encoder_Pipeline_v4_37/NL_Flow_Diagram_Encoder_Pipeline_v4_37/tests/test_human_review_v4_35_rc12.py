import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pycharm_runner import run_human_review_folder
from study_review import discover_sibling_review_roots


class HumanReviewRC12Tests(unittest.TestCase):
    def _write_questionnaire(self, root: Path, aid: int, dataset: str, *, is_baseline: bool = False):
        scoring = root / f"Algorithm - {aid}" / "pipeline_artifacts" / "scoring"
        scoring.mkdir(parents=True, exist_ok=True)
        payload = {
            "algorithm": {"algorithm_id": aid, "dataset": dataset, "is_baseline": is_baseline},
            "criteria": [],
        }
        (scoring / "human_review_questionnaire.json").write_text(json.dumps(payload), encoding="utf-8")
        return scoring

    def test_resume_discovery_finds_sibling_llm_datasets_and_excludes_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            study = Path(directory) / "Study"
            a_results = study / "Agent A" / "Results"
            b_results = study / "Agent B" / "Results"
            baseline_results = study / "Baselines" / "Results"
            self._write_questionnaire(a_results, 1, "Agent A")
            self._write_questionnaire(b_results, 1, "Agent B")
            self._write_questionnaire(baseline_results, 1, "Baseline", is_baseline=True)

            roots = discover_sibling_review_roots(study / "Agent A")
            self.assertEqual([a_results.resolve(), b_results.resolve()], roots)

    def test_start_fresh_does_not_discover_siblings(self):
        with tempfile.TemporaryDirectory() as directory:
            study = Path(directory) / "Study"
            a_results = study / "Agent A" / "Results"
            b_results = study / "Agent B" / "Results"
            self._write_questionnaire(a_results, 1, "Agent A")
            self._write_questionnaire(b_results, 1, "Agent B")

            with patch("pycharm_runner.launch_review_dashboard", return_value=True) as launch:
                result = run_human_review_folder(study / "Agent A", discover_siblings=False)

            launch.assert_called_once_with([study / "Agent A"])
            self.assertEqual("EXPLICIT_ONLY", result["discovery_mode"])

    def test_resume_mode_passes_all_discovered_roots_to_dashboard(self):
        with tempfile.TemporaryDirectory() as directory:
            study = Path(directory) / "Study"
            a_results = study / "Agent A" / "Results"
            b_results = study / "Agent B" / "Results"
            self._write_questionnaire(a_results, 1, "Agent A")
            self._write_questionnaire(b_results, 1, "Agent B")

            with patch("pycharm_runner.launch_review_dashboard", return_value=True) as launch:
                result = run_human_review_folder(study / "Agent B", discover_siblings=True)

            launch.assert_called_once_with([a_results.resolve(), b_results.resolve()])
            self.assertEqual("DISCOVER_SIBLINGS", result["discovery_mode"])
            self.assertEqual(2, len(result["review_roots"]))

    def test_recovery_mode_regenerates_central_dashboards_before_review_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            study = Path(directory) / "Study"
            a_results = study / "Agent A" / "Results"
            b_results = study / "Agent B" / "Results"
            self._write_questionnaire(a_results, 1, "Agent A")
            self._write_questionnaire(b_results, 1, "Agent B")

            with patch("pycharm_runner.StudyBatchProcessor.refresh_llm_drawio_views", return_value={"refreshed": 0, "errors": []}), \
                 patch("dashboard_generation.infer_study_root", return_value=study), \
                 patch("dashboard_generation.regenerate_study_dashboards", return_value={"individual_dashboards": ["A", "B"]}) as regenerate, \
                 patch("pycharm_runner.launch_review_dashboard", return_value=True):
                result = run_human_review_folder(
                    [a_results, b_results],
                    discover_siblings=False,
                    regenerate_dashboards=True,
                )

            regenerate.assert_called_once_with(study)
            self.assertEqual("REVIEW_SESSION_CLOSED", result["status"])



if __name__ == "__main__":
    unittest.main()
