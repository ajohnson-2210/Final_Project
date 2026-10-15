import unittest

from human_review import _html_document


class HumanReviewV436UITests(unittest.TestCase):
    def _template(self):
        return {
            "questionnaire_schema_version": "1.3",
            "rubric_version": "1.1",
            "pipeline_version": "4.37",
            "algorithm": {"algorithm_id": 1, "dataset": "Agent A", "source_file": "Algorithm 1.txt"},
            "instructions": "Review independently.",
            "reviewer": {"reviewer_id": "REV001", "reviewer_name": "Reviewer One", "overall_reviewer_confidence": None},
            "source_sufficiency": {
                "question": "Source sufficient?",
                "automated_result": "EVALUABLE",
                "automated_justification": "ok",
                "human_result": None,
                "agreement_with_automated_result": None,
                "reviewer_justification": "",
            },
            "behavioural_evidence_adequacy": {
                "question": "Evidence adequate?",
                "automated_result": "ADEQUATE",
                "summary": "ok",
                "coverage_dimensions": {},
                "strengths": [],
                "limitations": [],
                "coverage_basis": "tests",
                "interpretation": "ok",
                "human_result": None,
                "agreement_with_automated_result": None,
                "reviewer_justification": "",
            },
            "task_semantic_evaluation": {
                "instruction": "Judge semantics.",
                "contract": {"input": "x"},
                "automated_evidence": {"status": "ok"},
                "human_assessment": {
                    "required_inputs_represented": None,
                    "core_algorithm_logic": None,
                    "required_output_semantics_represented": None,
                    "edge_and_domain_handling": None,
                    "overall_semantic_assessment": None,
                    "reviewer_justification": "",
                },
            },
            "benchmark_validation": None,
            "criteria": [],
            "overall_review": {
                "material_semantic_error_not_captured": None,
                "first_semantic_loss_stage": None,
                "final_python_behaviourally_faithful": None,
                "additional_observations": "",
            },
        }

    def test_major_headings_are_title_case_and_coloured(self):
        html = _html_document(self._template())
        for heading in (
            "Source Sufficiency",
            "Behavioural Evidence Adequacy",
            "Task-Semantic Evaluation",
            "Stage Criteria",
            "Overall Review",
        ):
            self.assertIn(f"<h2>{heading}</h2>", html)
        self.assertIn("background:#2f6690", html)
        self.assertIn("border-left:5px solid #6c9bc3", html)

    def test_three_review_comments_use_presets_and_other_textarea(self):
        html = _html_document(self._template())
        for field in ("g1_justification", "g2_justification", "sem_justification"):
            self.assertIn(f'id="{field}_choice"', html)
            self.assertIn(f'id="{field}_other_wrap"', html)
            self.assertIn(f'id="{field}_other"', html)
        self.assertGreaterEqual(html.count("Other — add specific comment"), 3)
        self.assertIn("Evidence supports the selected assessment.", html)

    def test_existing_free_text_is_restored_through_other_logic(self):
        template = self._template()
        template["source_sufficiency"]["reviewer_justification"] = "Legacy source note"
        template["behavioural_evidence_adequacy"]["reviewer_justification"] = "Legacy evidence note"
        template["task_semantic_evaluation"]["human_assessment"]["reviewer_justification"] = "Legacy semantic note"
        html = _html_document(template)
        self.assertIn("setReviewComment('g1_justification',g1.reviewer_justification)", html)
        self.assertIn("setReviewComment('g2_justification',g2.reviewer_justification)", html)
        self.assertIn("setReviewComment('sem_justification',h.reviewer_justification)", html)
        self.assertIn("choice.value='__OTHER__'", html)


if __name__ == "__main__":
    unittest.main()
