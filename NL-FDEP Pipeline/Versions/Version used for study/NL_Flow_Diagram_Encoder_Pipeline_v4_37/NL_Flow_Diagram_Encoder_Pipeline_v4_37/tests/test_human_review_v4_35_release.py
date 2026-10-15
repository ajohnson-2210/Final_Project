import json
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from study_review import (
    _LocalReviewService,
    next_reviewer_id,
    review_status,
    reviewer_registry,
)


class HumanReviewReleaseTests(unittest.TestCase):
    def _questionnaire(self, scoring: Path, dataset: str = "Agent A") -> dict:
        scoring.mkdir(parents=True, exist_ok=True)
        document = {
            "questionnaire_schema_version": "1.3",
            "rubric_version": "1.1",
            "pipeline_version": "4.37",
            "algorithm": {"algorithm_id": 1, "dataset": dataset, "is_baseline": False, "source_file": "Algorithm 1.txt"},
            "instructions": "Independent human review.",
            "reviewer": {"reviewer_id": "", "reviewer_name": "", "reviewed_at_utc": None, "overall_reviewer_confidence": None},
            "source_sufficiency": {"question": "Source sufficient?", "automated_result": "EVALUABLE", "automated_justification": "ok", "human_result": None, "agreement_with_automated_result": None, "reviewer_justification": ""},
            "behavioural_evidence_adequacy": {"question": "Evidence adequate?", "automated_result": "ADEQUATE", "summary": "ok", "coverage_dimensions": {}, "strengths": [], "limitations": [], "coverage_basis": "tests", "interpretation": "ok", "human_result": None, "agreement_with_automated_result": None, "reviewer_justification": ""},
            "task_semantic_evaluation": None,
            "benchmark_validation": None,
            "criteria": [
                {
                    "criterion_id": "C1",
                    "stage_name": "Canonicalisation",
                    "question": "Preserved?",
                    "automated_score": 2,
                    "automated_status": "PASS",
                    "automated_confidence": "HIGH",
                    "automated_justification": "ok",
                    "evidence": [],
                    "human_assessment": {"score": None, "agreement_with_automated_score": None, "semantic_issue": None, "reviewer_justification": ""},
                }
            ],
            "overall_review": {"material_semantic_error_not_captured": None, "first_semantic_loss_stage": None, "final_python_behaviourally_faithful": None, "additional_observations": ""},
        }
        (scoring / "human_review_questionnaire.json").write_text(json.dumps(document), encoding="utf-8")
        return document

    def _payload(self, questionnaire: dict, reviewer_id: str, reviewer_name: str) -> dict:
        document = json.loads(json.dumps(questionnaire))
        document["reviewer"].update({"reviewer_id": reviewer_id, "reviewer_name": reviewer_name, "overall_reviewer_confidence": "HIGH"})
        document["criteria"][0]["human_assessment"].update({
            "score": 2,
            "score_label": "2",
            "completed": True,
            "agreement_with_automated_score": "AGREE",
            "semantic_issue": False,
            "reviewer_justification": "Confirmed.",
        })
        return document

    def _post(self, url: str, payload: dict):
        save_url = url.replace("/questionnaire/", "/save/")
        req = urllib.request.Request(
            save_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_next_reviewer_id_uses_study_registry(self):
        self.assertEqual("REV001", next_reviewer_id({}))
        self.assertEqual("REV004", next_reviewer_id({"REV001": "A", "REV003": "B"}))

    def test_registry_links_reviewer_id_to_name_across_sibling_datasets(self):
        with tempfile.TemporaryDirectory() as directory:
            study = Path(directory) / "Study"
            for agent in ("Agent A", "Agent B"):
                scoring = study / agent / "Results" / "Algorithm - 1" / "pipeline_artifacts" / "scoring"
                q = self._questionnaire(scoring, agent)
                if agent == "Agent B":
                    q["reviewer"].update({"reviewer_id": "REV002", "reviewer_name": "Reviewer Two"})
                    (scoring / "human_review.json").write_text(json.dumps(q), encoding="utf-8")
            registry, conflicts = reviewer_registry([study / "Agent A" / "Results"])
            self.assertEqual("Reviewer Two", registry["REV002"])
            self.assertEqual([], conflicts)

    def test_local_questionnaire_saves_directly_and_records_name(self):
        with tempfile.TemporaryDirectory() as directory:
            scoring = Path(directory) / "Results" / "Algorithm - 1" / "pipeline_artifacts" / "scoring"
            questionnaire = self._questionnaire(scoring)
            service = _LocalReviewService({})
            try:
                url = service.register(scoring, "REV001", "Reviewer One")
                with urllib.request.urlopen(url, timeout=5) as response:
                    html = response.read().decode("utf-8")
                self.assertIn("Reviewer Name", html)
                self.assertIn("Save review", html)
                with patch("study_review.adjudicate_files", return_value=None):
                    status, result = self._post(url, self._payload(questionnaire, "REV001", "Reviewer One"))
                self.assertEqual(200, status)
                self.assertTrue(result["ok"])
                saved = json.loads((scoring / "human_review.json").read_text(encoding="utf-8"))
                self.assertEqual("REV001", saved["reviewer"]["reviewer_id"])
                self.assertEqual("Reviewer One", saved["reviewer"]["reviewer_name"])
            finally:
                service.stop()

    def test_different_reviewer_cannot_overwrite_existing_review(self):
        with tempfile.TemporaryDirectory() as directory:
            scoring = Path(directory) / "Results" / "Algorithm - 1" / "pipeline_artifacts" / "scoring"
            questionnaire = self._questionnaire(scoring)
            existing = self._payload(questionnaire, "REV001", "Reviewer One")
            (scoring / "human_review.json").write_text(json.dumps(existing), encoding="utf-8")
            service = _LocalReviewService({"REV001": "Reviewer One", "REV002": "Reviewer Two"})
            try:
                url = service.register(scoring, "REV002", "Reviewer Two")
                with urllib.request.urlopen(url, timeout=5) as response:
                    html = response.read().decode("utf-8")
                self.assertIn("opened read-only", html)
                self.assertIn("Reviewer One", html)
                with patch("study_review.adjudicate_files", return_value=None):
                    with self.assertRaises(urllib.error.HTTPError) as error:
                        self._post(url, self._payload(questionnaire, "REV002", "Reviewer Two"))
                self.assertEqual(409, error.exception.code)
                unchanged = json.loads((scoring / "human_review.json").read_text(encoding="utf-8"))
                self.assertEqual("REV001", unchanged["reviewer"]["reviewer_id"])
            finally:
                service.stop()

    def test_same_reviewer_can_resume_and_status_reports_owner(self):
        with tempfile.TemporaryDirectory() as directory:
            results = Path(directory) / "Results"
            scoring = results / "Algorithm - 1" / "pipeline_artifacts" / "scoring"
            questionnaire = self._questionnaire(scoring)
            existing = self._payload(questionnaire, "REV001", "Reviewer One")
            (scoring / "human_review.json").write_text(json.dumps(existing), encoding="utf-8")
            service = _LocalReviewService({"REV001": "Reviewer One"})
            try:
                url = service.register(scoring, "REV001", "Reviewer One")
                with urllib.request.urlopen(url, timeout=5) as response:
                    html = response.read().decode("utf-8")
                self.assertIn("Reviewer One", html)
                self.assertNotIn("opened read-only", html)
                rows = review_status(results)
                self.assertEqual("COMPLETE", rows[0]["review_state"])
                self.assertEqual("REV001", rows[0]["reviewer_id"])
                self.assertEqual("Reviewer One", rows[0]["reviewer_name"])
            finally:
                service.stop()


if __name__ == "__main__":
    unittest.main()
