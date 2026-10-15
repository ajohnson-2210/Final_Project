import json
import tempfile
import unittest
from pathlib import Path

from adjudication import adjudicate_files
from pseudocode_profiles import PseudocodeProfile
from study_analysis import aggregate_algorithm_folders
from study_batch import StudyBatchProcessor


SAMPLE = '''total <- INTEGER(0)\nFOR i <- IN RANGE INTEGER(1) TO INTEGER(4) DO\ntotal <- total + i\nENDFOR\nOUTPUT total\n'''


class RubricSideBySideV435RC6Tests(unittest.TestCase):
    def _scored_folder(self, directory: str) -> tuple[Path, dict, dict]:
        root = Path(directory) / "source_a" / "results"
        folder = root / "Algorithm - 1"
        folder.mkdir(parents=True)
        (folder / "Algorithm 1 Pseudocode.txt").write_text(SAMPLE, encoding="utf-8")
        StudyBatchProcessor().process_llm_results(root, profile=PseudocodeProfile.AJ_DIALECT_STRICT)
        scoring = folder / "pipeline_artifacts" / "scoring"
        auto = json.loads((scoring / "automated_score.json").read_text(encoding="utf-8"))
        questionnaire = json.loads((scoring / "human_review_questionnaire.json").read_text(encoding="utf-8"))
        return scoring, auto, questionnaire

    def test_provisional_score_exposes_automated_rubric_but_no_combined_score(self):
        with tempfile.TemporaryDirectory() as directory:
            scoring, auto, _ = self._scored_folder(directory)
            final = json.loads((scoring / "final_score.json").read_text(encoding="utf-8"))
            self.assertEqual("1.5", auto["scoring_schema_version"])
            self.assertEqual("PROVISIONAL_AUTOMATED", final["score_status"])
            self.assertIsNotNone(final["rubric_scores"]["automated"]["percentage"])
            self.assertIsNone(final["rubric_scores"]["human"]["percentage"])
            self.assertFalse(final["rubric_scores"]["combined"]["available"])
            self.assertFalse(final["adjudication"]["criterion_substitution_used"])

    def test_partial_human_review_does_not_create_combined_score_or_replace_automated(self):
        with tempfile.TemporaryDirectory() as directory:
            scoring, auto, questionnaire = self._scored_folder(directory)
            questionnaire["reviewer"]["reviewer_id"] = "R1"
            first = questionnaire["criteria"][0]
            first["human_assessment"].update({
                "score": 0,
                "score_label": "0",
                "agreement_with_automated_score": "DISAGREE",
                "semantic_issue": True,
                "reviewer_justification": "Deliberate regression check.",
            })
            (scoring / "human_review.json").write_text(json.dumps(questionnaire), encoding="utf-8")
            adjudicate_files(scoring)
            final = json.loads((scoring / "final_score.json").read_text(encoding="utf-8"))
            criterion = final["stages"]["canonicalisation"]["criteria"][0]
            self.assertEqual(auto["stages"]["canonicalisation"]["criteria"][0]["automated_assessment"]["score"], criterion["automated_assessment"]["score"])
            self.assertEqual(0, criterion["human_assessment"]["score"])
            self.assertNotIn("final_assessment", criterion)
            self.assertEqual("HUMAN_REVIEW_PARTIAL", final["score_status"])
            self.assertEqual(1, final["rubric_scores"]["human"]["criteria_completed"])
            self.assertFalse(final["rubric_scores"]["combined"]["available"])
            self.assertIsNone(final["rubric_scores"]["combined"]["percentage"])

    def test_complete_human_rubric_produces_equal_weight_overall_average(self):
        with tempfile.TemporaryDirectory() as directory:
            scoring, auto, questionnaire = self._scored_folder(directory)
            questionnaire["reviewer"]["reviewer_id"] = "R1"
            for item in questionnaire["criteria"]:
                item["human_assessment"].update({
                    "score": 1,
                    "score_label": "1",
                    "agreement_with_automated_score": "PARTIALLY_AGREE",
                    "semantic_issue": False,
                    "reviewer_justification": "Independent human midpoint score for combination test.",
                })
            (scoring / "human_review.json").write_text(json.dumps(questionnaire), encoding="utf-8")
            adjudicate_files(scoring)
            final = json.loads((scoring / "final_score.json").read_text(encoding="utf-8"))

            automated_pct = final["rubric_scores"]["automated"]["percentage"]
            human_pct = final["rubric_scores"]["human"]["percentage"]
            expected = round((automated_pct + human_pct) / 2.0, 2)
            self.assertEqual(50.0, human_pct)
            self.assertEqual(expected, final["rubric_scores"]["combined"]["percentage"])
            self.assertTrue(final["rubric_scores"]["combined"]["available"])
            self.assertEqual("AUTOMATED_HUMAN_COMBINED", final["score_status"])
            self.assertEqual("EQUAL_WEIGHT_AUTOMATED_AND_HUMAN_RUBRIC_PERCENTAGES", final["adjudication"]["final_score_source"])
            self.assertFalse(final["adjudication"]["criterion_substitution_used"])

            # Behavioural metrics remain outside the rubric combination.
            self.assertEqual(auto["behavioural_testing"], final["behavioural_testing"])

            results_root = scoring.parents[2]
            outputs = aggregate_algorithm_folders(results_root)
            rows = json.loads(Path(outputs["algorithm_scores_json"]).read_text(encoding="utf-8"))
            row = next(row for row in rows if row.get("Algorithm") == 1)
            self.assertEqual(automated_pct, row["AutomatedRubricPercent"])
            self.assertEqual(human_pct, row["HumanRubricPercent"])
            self.assertEqual(expected, row["CombinedRubricPercent"])
            self.assertTrue(row["HumanRubricComplete"])
            self.assertEqual(final["behavioural_testing"]["accuracy_percentage"], row["TestAccuracyPercent"])

    def test_returned_human_review_is_combined_on_resume_without_reprocessing_pipeline(self):
        with tempfile.TemporaryDirectory() as directory:
            scoring, _, questionnaire = self._scored_folder(directory)
            questionnaire["reviewer"]["reviewer_id"] = "R1"
            for item in questionnaire["criteria"]:
                auto = item.get("automated_score")
                if auto is None:
                    item["human_assessment"].update({
                        "score": None,
                        "score_label": "NA",
                        "agreement_with_automated_score": "AGREE",
                        "semantic_issue": False,
                        "reviewer_justification": "Not applicable in both streams.",
                    })
                else:
                    item["human_assessment"].update({
                        "score": int(auto),
                        "score_label": str(int(auto)),
                        "agreement_with_automated_score": "AGREE",
                        "semantic_issue": False,
                        "reviewer_justification": "Independent review agrees for resume test.",
                    })
            (scoring / "human_review.json").write_text(json.dumps(questionnaire), encoding="utf-8")

            results_root = scoring.parents[2]
            drawio = scoring.parent / "flow_diagram.drawio"
            drawio.write_text("STALE REVIEWED DRAWIO", encoding="utf-8")
            rerun = StudyBatchProcessor().process_llm_results(results_root, profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            record = next(item for item in rerun["report"]["algorithms"] if item["algorithm_id"] == 1)
            self.assertEqual("SKIPPED_REVIEWED", record["action"])
            self.assertNotEqual("STALE REVIEWED DRAWIO", drawio.read_text(encoding="utf-8"))
            self.assertIn("<mxfile", drawio.read_text(encoding="utf-8"))
            final = json.loads((scoring / "final_score.json").read_text(encoding="utf-8"))
            self.assertEqual("AUTOMATED_HUMAN_COMBINED", final["score_status"])
            self.assertTrue(final["rubric_scores"]["combined"]["available"])
            self.assertEqual(final["rubric_scores"]["automated"]["percentage"], final["rubric_scores"]["human"]["percentage"])
            self.assertEqual(final["rubric_scores"]["automated"]["percentage"], final["rubric_scores"]["combined"]["percentage"])


if __name__ == "__main__":
    unittest.main()
