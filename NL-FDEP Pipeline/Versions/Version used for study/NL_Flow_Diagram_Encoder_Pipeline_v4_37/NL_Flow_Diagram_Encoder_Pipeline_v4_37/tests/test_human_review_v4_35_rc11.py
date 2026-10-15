import json
import tempfile
import unittest
from pathlib import Path

from study_review import discover_review_datasets, normalise_review_root, review_status


class HumanReviewRC11Tests(unittest.TestCase):
    def _write_questionnaire(self, root: Path, aid: int, dataset: str, *, is_baseline: bool = False):
        scoring = root / f"Algorithm - {aid}" / "pipeline_artifacts" / "scoring"
        scoring.mkdir(parents=True, exist_ok=True)
        payload = {
            "algorithm": {"algorithm_id": aid, "dataset": dataset, "is_baseline": is_baseline},
            "criteria": [],
        }
        (scoring / "human_review_questionnaire.json").write_text(json.dumps(payload), encoding="utf-8")
        (scoring / "human_review_questionnaire.html").write_text("<html></html>", encoding="utf-8")
        return scoring

    def test_outer_llm_folder_normalises_to_results(self):
        with tempfile.TemporaryDirectory() as directory:
            outer = Path(directory) / "Agent A"
            results = outer / "Results"
            self._write_questionnaire(results, 1, "Agent A")
            self.assertEqual(results.resolve(), normalise_review_root(outer).resolve())

    def test_algorithm_rows_are_sorted_numerically(self):
        with tempfile.TemporaryDirectory() as directory:
            results = Path(directory) / "Results"
            for aid in (10, 2, 1, 50, 11):
                self._write_questionnaire(results, aid, "Agent A")
            self.assertEqual([1, 2, 10, 11, 50], [row["algorithm_id"] for row in review_status(results)])

    def test_baseline_questionnaires_are_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            pseudo = Path(directory) / "Pseudocode"
            self._write_questionnaire(pseudo, 1, "Baseline", is_baseline=True)
            self.assertEqual([], review_status(pseudo))
            self.assertEqual([], discover_review_datasets([pseudo]))

    def test_session_registry_contains_all_llm_datasets_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            a_outer = base / "Agent A"; a_results = a_outer / "Results"
            b_outer = base / "Agent B"; b_results = b_outer / "Results"
            for aid in (1, 2):
                self._write_questionnaire(a_results, aid, "Agent A")
                self._write_questionnaire(b_results, aid, "Agent B")
            datasets = discover_review_datasets([a_outer, b_results, a_results])
            self.assertEqual(["Agent A", "Agent B"], [item["name"] for item in datasets])
            self.assertEqual([2, 2], [len(item["rows"]) for item in datasets])


if __name__ == "__main__":
    unittest.main()
