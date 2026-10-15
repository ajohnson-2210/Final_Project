from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dashboard_generation import (
    generate_dashboards_for_completed_batch,
    update_study_algorithm_count_consistency,
)
from pycharm_runner import _report_llm_dataset_consistency


class _Dialog:
    def __init__(self):
        self.messages = []

    def show_info(self, title: str, message: str) -> None:
        self.messages.append((title, message))


def _write_batch(study: Path, dataset: str, count: int, ids: list[int] | None = None) -> tuple[Path, Path]:
    results = study / dataset / "Results"
    analysis = results / "study_analysis"
    analysis.mkdir(parents=True, exist_ok=True)
    ids = ids if ids is not None else list(range(1, count + 1))
    report = {
        "batch_type": "LLM_RESULTS",
        "dataset": dataset,
        "algorithm_count": count,
        "mean_experimental_behavioural_percentage": 80.0,
        "semantic_test_accuracy_percentage": 75.0,
        "algorithms": [
            {
                "algorithm_id": aid,
                "experimental_behavioural_percentage": 100.0,
                "status": "SUCCESS",
            }
            for aid in ids
        ],
    }
    (analysis / "batch_report.json").write_text(json.dumps(report), encoding="utf-8")
    (analysis / "algorithm_scores.json").write_text("[]", encoding="utf-8")
    return results, analysis


class DynamicStudyAlgorithmCountV437Tests(unittest.TestCase):
    def test_first_llm_dataset_establishes_n_and_dashboards_use_dynamic_denominator(self):
        with tempfile.TemporaryDirectory() as td:
            study = Path(td)
            results, analysis = _write_batch(study, "Agent A", 3)

            status = generate_dashboards_for_completed_batch(results, analysis, "LLM_RESULTS")

            self.assertEqual(3, status["expected_algorithm_count"])
            self.assertEqual("CONSISTENT", status["dataset_consistency_status"])
            self.assertEqual(0, status["dataset_mismatch_count"])
            consistency_path = study / "analysis" / "study_dataset_consistency.json"
            self.assertEqual(consistency_path, Path(status["dataset_consistency_file"]))
            consistency = json.loads(consistency_path.read_text(encoding="utf-8"))
            self.assertEqual(3, consistency["expected_algorithm_count"])
            self.assertEqual([1, 2, 3], consistency["expected_algorithm_ids"])
            self.assertEqual("Agent A", consistency["reference_dataset"])

            comparative = Path(status["comparative_dashboard"])
            self.assertEqual(comparative, Path(status["interactive_heatmap_dashboard"]))
            self.assertIn("3 study algorithms", comparative.read_text(encoding="utf-8"))
            self.assertFalse(
                (study / "analysis" / "dashboards" / "NL_FDEP_interactive_heatmap_dashboard_v5.html").exists()
            )
            profiles = Path(status["radial_profiles_dashboard"])
            self.assertEqual(
                study / "analysis" / "dashboards" / "NL-FDEP All AI Agents - 3-Algorithm Radial Profiles.html",
                profiles,
            )
            self.assertIn("3-Algorithm Radial Profiles", profiles.read_text(encoding="utf-8"))

            final_text = Path(status["final_scoring_dashboard"]).read_text(encoding="utf-8")
            self.assertIn("3 / 3 terminal Human Review outcomes required", final_text)
            self.assertIn('"humanReviewsRequired":3', final_text)
            self.assertIn("fixed denominator N", final_text)

    def test_later_count_mismatch_warns_and_does_not_redefine_n(self):
        with tempfile.TemporaryDirectory() as td:
            study = Path(td)
            a_results, a_analysis = _write_batch(study, "Agent A", 3)
            generate_dashboards_for_completed_batch(a_results, a_analysis, "LLM_RESULTS")

            b_results, b_analysis = _write_batch(study, "Agent B", 2)
            status = generate_dashboards_for_completed_batch(b_results, b_analysis, "LLM_RESULTS")
            self.assertEqual(3, status["expected_algorithm_count"])
            self.assertEqual("MISMATCH", status["dataset_consistency_status"])
            self.assertEqual(1, status["dataset_mismatch_count"])

            consistency = update_study_algorithm_count_consistency(study)
            b = next(x for x in consistency["datasets"] if x["dataset"] == "Agent B")
            self.assertFalse(b["count_match"])
            self.assertEqual(2, b["algorithm_count"])
            self.assertEqual(3, b["expected_algorithm_count"])

            dialog = _Dialog()
            _report_llm_dataset_consistency(dialog, {
                "report": {"batch_type": "LLM_RESULTS", "dataset": "Agent B", "algorithm_count": 2},
                "json_path": str(b_analysis / "batch_report.json"),
            })
            self.assertEqual(1, len(dialog.messages))
            title, message = dialog.messages[0]
            self.assertIn("mismatch", title.lower())
            self.assertIn("Study algorithm count N: 3", message)
            self.assertIn("Algorithms found: 2", message)
            self.assertIn("N has NOT been changed", message)

            # Reprocessing the original dataset with a different count cannot
            # silently redefine an already-established study denominator.
            _write_batch(study, "Agent A", 4)
            consistency = update_study_algorithm_count_consistency(study)
            self.assertEqual(3, consistency["expected_algorithm_count"])
            self.assertEqual("Agent A", consistency["reference_dataset"])

    def test_equal_count_but_different_algorithm_ids_is_also_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            study = Path(td)
            a_results, a_analysis = _write_batch(study, "Agent A", 3, [1, 2, 3])
            generate_dashboards_for_completed_batch(a_results, a_analysis, "LLM_RESULTS")
            _write_batch(study, "Agent B", 3, [1, 2, 4])

            consistency = update_study_algorithm_count_consistency(study)
            b = next(x for x in consistency["datasets"] if x["dataset"] == "Agent B")
            self.assertTrue(b["count_match"])
            self.assertTrue(b["id_set_checked"])
            self.assertFalse(b["id_set_match"])
            self.assertEqual([3], b["missing_algorithm_ids"])
            self.assertEqual([4], b["extra_algorithm_ids"])
            self.assertEqual("MISMATCH", b["status"])


if __name__ == "__main__":
    unittest.main()
