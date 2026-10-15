import json
import tempfile
import unittest
from pathlib import Path

from aj_test_harness import AJTestHarness
from baseline_benchmark import test_cases_from_spec as build_test_cases
from pseudocode_profiles import PseudocodeProfile
from study_batch import StudyBatchProcessor
from study_rubric import RUBRIC_VERSION, PIPELINE_VERSION, rubric_document


class CommonBehaviouralTestsV422(unittest.TestCase):
    def test_seeded_reference_and_generated_execution_are_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "reference.py"
            generated = root / "generated.py"
            source = "import random\nprint(random.randint(1, 1000000))\n"
            reference.write_text(source, encoding="utf-8")
            generated.write_text(source, encoding="utf-8")
            specs = [{
                "name": "seeded",
                "random_seed": 104729,
                "category": "NORMAL",
                "criteria_links": ["P2", "P4"],
            }]
            cases, records = build_test_cases(specs, reference_python=reference)
            self.assertEqual(["226191"], cases[0].expected_output)
            self.assertEqual(104729, cases[0].random_seed)
            report = AJTestHarness().run(generated, cases)
            self.assertTrue(report.success)
            self.assertEqual(["226191"], report.results[0].actual_output)
            self.assertEqual(["P2", "P4"], report.results[0].criteria_links)
            self.assertEqual("REFERENCE_PYTHON", records[0]["expected_result_source"])

    def test_unavailable_declared_reference_dependency_is_not_used_as_oracle(self):
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / "reference.py"
            reference.write_text("print('never reached')\n", encoding="utf-8")
            specs = [{"name": "dependency", "requires_modules": ["module_that_does_not_exist_nlfdep"]}]
            cases, records = build_test_cases(specs, reference_python=reference)
            self.assertEqual([], cases)
            self.assertEqual("MISSING_DEPENDENCY", records[0]["reference"]["status"])
            self.assertEqual("NOT_EVALUABLE", records[0]["test_case_status"])

    def test_rubric_v11_adds_non_scored_g2_without_changing_core_criteria(self):
        rubric = rubric_document()
        self.assertEqual("4.37", PIPELINE_VERSION)
        self.assertEqual("1.1", RUBRIC_VERSION)
        self.assertFalse(rubric["behavioural_evidence_gate"]["scored"])
        self.assertEqual("G2", rubric["behavioural_evidence_gate"]["criterion_id"])
        self.assertIn("summary", rubric["behavioural_evidence_gate"]["required_descriptive_fields"])
        self.assertIn("coverage_dimensions", rubric["behavioural_evidence_gate"]["required_descriptive_fields"])
        criteria = []
        for stage in rubric["stages"].values():
            criteria.extend(c["criterion_id"] for c in stage["criteria"])
        self.assertEqual(
            ["C1","C2","C3","C4","A1","A2","A3","A4","F1","F2","F3","F4","P1","P2","P3","P4"],
            criteria,
        )

    def test_suite_metadata_and_termination_category_reach_scoring(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "Baseline"
            pseudo = baseline / "pseudocode" / "Algorithm - 1"
            py = baseline / "python" / "Algorithm - 1"
            pseudo.mkdir(parents=True)
            py.mkdir(parents=True)
            (pseudo / "Algorithm 1 Pseudocode.txt").write_text('OUTPUT STRING("bye")\n', encoding="utf-8")
            (py / "Algorithm 1 Baseline Python code.txt").write_text('print("bye")\n', encoding="utf-8")
            (py / "Algorithm 1 Tests.json").write_text(json.dumps({
                "test_spec_schema_version": "1.1",
                "algorithm_id": 1,
                "evidence_adequacy": "ADEQUATE",
                "coverage_limitations": [],
                "tests": [{
                    "name": "termination evidence",
                    "standard_input": [],
                    "category": "TERMINATION",
                    "semantic_feature": "PROGRAM_TERMINATION",
                    "criteria_links": ["P2", "P3", "P4"],
                }],
            }), encoding="utf-8")
            result = StudyBatchProcessor(common_tests_root=Path(directory) / "no_common_tests").process_baseline(
                baseline,
                profile=PseudocodeProfile.AJ_DIALECT_STRICT,
            )
            self.assertEqual({"SUCCESS": 1}, result["report"]["pipeline_status_counts"])
            artifacts = pseudo / "pipeline_artifacts"
            evidence = json.loads((artifacts / "test_suite_evidence.json").read_text(encoding="utf-8"))
            self.assertEqual("ADEQUATE", evidence["declared_evidence_adequacy"])
            score = json.loads((artifacts / "scoring" / "automated_score.json").read_text(encoding="utf-8"))
            g2 = score["behavioural_evidence_adequacy"]
            self.assertEqual("ADEQUATE", g2["result"])
            self.assertTrue(g2["summary"])
            self.assertEqual(1, g2["test_counts"]["declared"])
            self.assertEqual(1, g2["test_counts"]["evaluable"])
            self.assertEqual(1, g2["test_counts"]["passed"])
            self.assertEqual("PARTIALLY_COVERED", g2["coverage_dimensions"]["termination_behaviour"]["status"])
            self.assertEqual("NOT_COVERED", g2["coverage_dimensions"]["branch_behaviour"]["status"])
            self.assertTrue(g2["strengths"])
            self.assertTrue(g2["coverage_basis"])
            self.assertTrue(g2["interpretation"])
            self.assertEqual(100.0, score["behavioural_testing"]["category_metrics"]["TERMINATION"]["accuracy_percentage"])
            p3 = next(c for c in score["stages"]["python"]["criteria"] if c["criterion_id"] == "P3")
            self.assertEqual(2, p3["automated_assessment"]["score"])
            questionnaire = json.loads((artifacts / "scoring" / "human_review_questionnaire.json").read_text(encoding="utf-8"))
            self.assertIn("coverage_dimensions", questionnaire["behavioural_evidence_adequacy"])
            rows = json.loads((baseline / "study_analysis" / "algorithm_scores.json").read_text(encoding="utf-8"))
            self.assertEqual("ADEQUATE", rows[0]["BehaviouralEvidenceAdequacy"])
            self.assertTrue(rows[0]["G2Summary"])
            self.assertEqual("PARTIALLY_COVERED", rows[0]["G2TerminationCoverage"])

    def test_g2_preserves_declared_description_and_reports_runtime_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "Baseline"
            pseudo = baseline / "pseudocode" / "Algorithm - 1"
            py = baseline / "python" / "Algorithm - 1"
            pseudo.mkdir(parents=True)
            py.mkdir(parents=True)
            (pseudo / "Algorithm 1 Pseudocode.txt").write_text('OUTPUT STRING("ok")\n', encoding="utf-8")
            (py / "Algorithm 1 Baseline Python code.txt").write_text('print("ok")\n', encoding="utf-8")
            (py / "Algorithm 1 Tests.json").write_text(json.dumps({
                "test_spec_schema_version": "1.2",
                "algorithm_id": 1,
                "evidence_adequacy": "LIMITED",
                "evidence_summary": "The frozen interface exposes one fixed normal-path scenario.",
                "coverage_dimensions": {
                    "normal_path": "COVERED",
                    "branch_behaviour": "NOT_APPLICABLE"
                },
                "coverage_basis": "Declared from the frozen program interface and common-test design.",
                "interpretation_guidance": "Interpret perfect agreement only for the fixed scenario exercised by this suite.",
                "coverage_limitations": ["Alternate inputs cannot be injected without changing the frozen source."],
                "tests": [{
                    "name": "fixed scenario",
                    "standard_input": [],
                    "category": "NORMAL",
                    "criteria_links": ["P2", "P4"]
                }]
            }), encoding="utf-8")
            StudyBatchProcessor(common_tests_root=Path(directory) / "no_common_tests").process_baseline(baseline, profile=PseudocodeProfile.AJ_DIALECT_STRICT)
            score = json.loads((pseudo / "pipeline_artifacts" / "scoring" / "automated_score.json").read_text(encoding="utf-8"))
            g2 = score["behavioural_evidence_adequacy"]
            self.assertEqual("LIMITED", g2["result"])
            self.assertIn("fixed normal-path scenario", g2["summary"])
            self.assertEqual("COVERED", g2["coverage_dimensions"]["normal_path"]["status"])
            self.assertEqual("NOT_APPLICABLE", g2["coverage_dimensions"]["branch_behaviour"]["status"])
            self.assertIn("Alternate inputs", g2["limitations"][0])
            self.assertIn("perfect agreement", g2["interpretation"])


if __name__ == "__main__":
    unittest.main()
