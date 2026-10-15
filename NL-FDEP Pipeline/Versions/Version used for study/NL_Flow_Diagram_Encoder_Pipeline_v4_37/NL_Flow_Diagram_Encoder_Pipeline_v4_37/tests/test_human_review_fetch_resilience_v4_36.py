import inspect
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from human_review import _html_document
import study_review


class HumanReviewFetchResilienceTests(unittest.TestCase):
    def _template(self):
        return {
            "algorithm": {"algorithm_id": 27, "dataset": "Agent", "is_baseline": False},
            "instructions": "Independent review.",
            "reviewer": {"reviewer_id": "REV001", "reviewer_name": "Reviewer One"},
            "source_sufficiency": {},
            "behavioural_evidence_adequacy": {},
            "task_semantic_evaluation": None,
            "benchmark_validation": None,
            "criteria": [],
            "overall_review": {},
        }

    def test_server_backed_questionnaire_preserves_review_if_fetch_service_is_unavailable(self):
        html = _html_document(self._template(), save_endpoint="/save/token")
        self.assertIn("function downloadReviewBackup(review)", html)
        self.assertIn("downloadReviewBackup(review);showStatus(false,\"Direct save service is unavailable.", html)
        self.assertIn("algorithm's pipeline_artifacts/scoring folder.\"", html)
        self.assertNotIn("Review could not be saved: '+err", html)
        self.assertIn("cache:'no-store'", html)

    def test_rendered_server_questionnaire_has_valid_javascript_and_identity_payload(self):
        html = _html_document(
            self._template(),
            reviewer_identity={"reviewer_id": "REV007", "reviewer_name": "AJ"},
            save_endpoint="/save/token",
        )
        template_match = re.search(r'<script id="template" type="application/json">(.*?)</script>', html, re.S)
        self.assertIsNotNone(template_match)
        embedded = json.loads(template_match.group(1))
        self.assertEqual("REV007", embedded["reviewer"]["reviewer_id"])
        self.assertEqual("AJ", embedded["reviewer"]["reviewer_name"])
        self.assertIn("setVal('reviewer_id',r.reviewer_id)", html)
        self.assertIn("setVal('reviewer_name',r.reviewer_name)", html)

        node = shutil.which("node")
        if node is None:
            self.skipTest("Node.js is unavailable for rendered questionnaire syntax validation.")
        script_match = re.search(r'<script>\n(.*)\n</script>', html, re.S)
        self.assertIsNotNone(script_match)
        with tempfile.TemporaryDirectory() as directory:
            script_path = Path(directory) / "questionnaire.js"
            script_path.write_text(script_match.group(1), encoding="utf-8")
            result = subprocess.run([node, "--check", str(script_path)], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_window_manager_close_does_not_stop_open_questionnaire_service(self):
        source = inspect.getsource(study_review.launch_review_dashboard)
        self.assertIn("if service.contexts:\n            root.iconify()\n            return", source)
        self.assertIn('text="End Review Session"', source)
        self.assertIn("end_session_button.config(command=end_review_session)", source)


if __name__ == "__main__":
    unittest.main()
