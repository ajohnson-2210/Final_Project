import json
import unittest
from pathlib import Path

from common_test_resources import DEFAULT_COMMON_TESTS_ROOT, TEST_DESIGN_VERSION
from human_review import JUSTIFICATION_PRESETS, _html_document


class QuestionnaireEfficiencyTests(unittest.TestCase):
    def _template(self):
        return {
            "questionnaire_schema_version": "1.3",
            "rubric_version": "1.1",
            "pipeline_version": "4.37",
            "algorithm": {"algorithm_id": 1, "dataset": "Agent A", "is_baseline": False, "source_file": "Algorithm 1.txt"},
            "instructions": "Independent human review.",
            "reviewer": {"reviewer_id": "REV001", "reviewer_name": "Reviewer One", "reviewed_at_utc": None, "overall_reviewer_confidence": None},
            "source_sufficiency": {"question": "Source sufficient?", "automated_result": "EVALUABLE", "automated_justification": "ok", "human_result": None, "agreement_with_automated_result": None, "reviewer_justification": ""},
            "behavioural_evidence_adequacy": {"question": "Evidence adequate?", "automated_result": "ADEQUATE", "summary": "ok", "coverage_dimensions": {}, "strengths": [], "limitations": [], "coverage_basis": "tests", "interpretation": "ok", "human_result": None, "agreement_with_automated_result": None, "reviewer_justification": ""},
            "task_semantic_evaluation": None,
            "benchmark_validation": None,
            "criteria": [{
                "criterion_id": "C1", "stage_name": "Canonicalisation", "question": "Preserved?",
                "automated_score": 2, "automated_status": "PASS", "automated_confidence": "HIGH",
                "automated_justification": "ok", "evidence": [],
                "human_assessment": {"score": None, "agreement_with_automated_score": None, "semantic_issue": None, "reviewer_justification": ""},
            }],
            "overall_review": {"material_semantic_error_not_captured": None, "first_semantic_loss_stage": None, "final_python_behaviourally_faithful": None, "additional_observations": ""},
        }

    def test_stage_justification_uses_presets_and_other_comment(self):
        html = _html_document(self._template())
        self.assertIn('criterion_0_justification_choice', html)
        self.assertIn(JUSTIFICATION_PRESETS[0], html)
        self.assertIn('Other — add specific comment', html)
        self.assertIn('criterion_0_justification_other', html)
        self.assertIn("criterionJustification(i)", html)
        self.assertIn("choice.value='__OTHER__'", html)

    def test_active_common_tests_are_v142_with_algorithm_1_wording_fix(self):
        self.assertEqual("1.4.2", TEST_DESIGN_VERSION)
        active = json.loads((DEFAULT_COMMON_TESTS_ROOT / "Algorithm - 1" / "Algorithm 1 Tests.json").read_text(encoding="utf-8"))
        self.assertEqual("1.4.2", active["test_design_version"])
        self.assertEqual(
            "True if both strings contain the same multiset of characters.",
            active["semantic_contract"]["result"]["canonical_semantics"],
        )
        historical_root = DEFAULT_COMMON_TESTS_ROOT.parent / "common tests v1.4.1"
        historical = json.loads((historical_root / "Algorithm - 1" / "Algorithm 1 Tests.json").read_text(encoding="utf-8"))
        self.assertEqual(
            "True iff both strings contain the same multiset of characters.",
            historical["semantic_contract"]["result"]["canonical_semantics"],
        )


if __name__ == "__main__":
    unittest.main()
