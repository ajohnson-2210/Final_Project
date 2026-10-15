from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from baseline_benchmark import load_test_spec, load_test_suite_metadata
from common_test_resources import DEFAULT_COMMON_TESTS_ROOT, TEST_DESIGN_VERSION, TEST_SPEC_SCHEMA_VERSION
from semantic_evaluation import SemanticTestHarness
from study_batch import StudyBatchProcessor
from pseudocode_profiles import PseudocodeProfile
import pycharm_runner

ROOT = Path(__file__).resolve().parents[1]


class FrozenSemanticIntegrityV435Tests(unittest.TestCase):
    def test_pack_is_static_and_contains_no_runtime_oracle_fields(self):
        self.assertEqual("1.4.2", TEST_DESIGN_VERSION)
        self.assertEqual("1.6", TEST_SPEC_SCHEMA_VERSION)
        enabled = 0
        for aid in range(1, 51):
            path = DEFAULT_COMMON_TESTS_ROOT / f"Algorithm - {aid}" / f"Algorithm {aid} Tests.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            contract = data["semantic_contract"]
            self.assertTrue(contract["runtime_oracle_prohibited"])
            self.assertNotIn("baseline_source_sha256", contract)
            self.assertNotIn("baseline_fixture_source", contract)
            for case in data["tests"]:
                sem = case.get("semantic_test") or {}
                self.assertNotIn("oracle_source", sem)
                if sem.get("enabled"):
                    enabled += 1
                    stream = str(case.get("score_stream") or sem.get("score_stream") or "CORE_BEHAVIOURAL").upper()
                    if stream == "SEMANTIC_BOUNDARY_PROBE":
                        self.assertEqual("BOUNDARY_OBSERVATION", sem.get("expectation_policy"))
                        self.assertNotIn("expected_semantic_result", sem)
                    elif stream == "PRE_FREEZE_VALIDATION":
                        self.assertEqual("PROVISIONAL_PRE_FREEZE_VALUE", sem.get("expectation_policy"))
                        self.assertIn("expected_semantic_result", sem)
                        self.assertIsInstance(sem.get("observer"), dict)
                    else:
                        self.assertEqual("STATIC_FROZEN_VALUE", sem.get("expectation_policy"))
                        self.assertIn("expected_semantic_result", sem)
                        self.assertIsInstance(sem.get("observer"), dict)
        self.assertEqual(124, enabled)

    def test_runtime_semantic_evaluator_has_no_algorithm_specific_dispatch(self):
        text = (ROOT / "study components" / "semantic_evaluation.py").read_text(encoding="utf-8")
        self.assertNotIn("algorithm_id ==", text)
        self.assertNotIn("algorithm_id in", text)

    def test_algorithm1_accepts_canonical_boolean_return(self):
        with tempfile.TemporaryDirectory() as td:
            program = Path(td) / "program.py"
            program.write_text("def check(a,b):\n    return sorted(a)==sorted(b)\n", encoding="utf-8")
            suite = DEFAULT_COMMON_TESTS_ROOT / "Algorithm - 1" / "Algorithm 1 Tests.json"
            report = SemanticTestHarness().run(program,1,load_test_suite_metadata(suite),load_test_spec(suite))
            self.assertEqual(100.0, report.accuracy_percentage)

    def test_tree_fixture_is_representation_neutral_and_grouping_is_required(self):
        with tempfile.TemporaryDirectory() as td:
            program = Path(td) / "program.py"
            program.write_text(
                "def level(root):\n"
                "    q=[root]; out=[]\n"
                "    while q:\n"
                "        level=[]; nxt=[]\n"
                "        for n in q:\n"
                "            level.append(n.value)\n"
                "            if n.left is not None: nxt.append(n.left)\n"
                "            if n.right is not None: nxt.append(n.right)\n"
                "        out.append(level); q=nxt\n"
                "    return out\n", encoding="utf-8")
            suite=DEFAULT_COMMON_TESTS_ROOT/"Algorithm - 26"/"Algorithm 26 Tests.json"
            report=SemanticTestHarness().run(program,26,load_test_suite_metadata(suite),load_test_spec(suite))
            self.assertEqual(100.0,report.accuracy_percentage)

    def test_class_operation_sequences_are_automated_without_model_specific_names(self):
        with tempfile.TemporaryDirectory() as td:
            stack=Path(td)/"stack.py"
            stack.write_text(
                "class AnyStack:\n"
                "    def __init__(self): self.v=[]\n"
                "    def push(self,x): self.v.append(x)\n"
                "    def pop(self): return self.v.pop() if self.v else None\n"
                "    def peek(self): return self.v[-1] if self.v else None\n", encoding="utf-8")
            suite=DEFAULT_COMMON_TESTS_ROOT/"Algorithm - 37"/"Algorithm 37 Tests.json"
            report=SemanticTestHarness().run(stack,37,load_test_suite_metadata(suite),load_test_spec(suite))
            self.assertEqual(100.0,report.accuracy_percentage)

    def test_experimental_scoring_is_identical_with_or_without_supplied_baseline(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            results=base/"model"/"results"; alg=results/"Algorithm - 1"; alg.mkdir(parents=True)
            (alg/"Algorithm 1 Pseudocode.txt").write_text(
                "FUNCTION check ACCEPTS(a, b)\n    RETURN BOOLEAN(FALSE)\nENDFUNCTION\n", encoding="utf-8")
            fake=base/"fake_baseline"; (fake/"python"/"Algorithm - 1").mkdir(parents=True)
            (fake/"python"/"Algorithm - 1"/"Algorithm 1 Baseline Python code.txt").write_text("print('wrong')\n")
            first=StudyBatchProcessor().process_llm_results(results,profile=PseudocodeProfile.AJ_DIALECT_STRICT,baseline_root=fake,force=True)
            score1=first["report"]["algorithms"][0]["experimental_behavioural_percentage"]
            second=StudyBatchProcessor().process_llm_results(results,profile=PseudocodeProfile.AJ_DIALECT_STRICT,baseline_root=None,force=True)
            score2=second["report"]["algorithms"][0]["experimental_behavioural_percentage"]
            self.assertEqual(score1,score2)
            comparison=json.loads((alg/"pipeline_artifacts"/"baseline_relative_comparison.json").read_text())
            self.assertFalse(comparison["runtime_baseline_reference_used"])
            self.assertIsNone(comparison["reference_python"])

    def test_llm_route_uses_baseline_only_as_procedural_readiness_gate(self):
        self.assertEqual({pycharm_runner.InputRoute.LLM_RESULTS_FOLDER}, pycharm_runner.BASELINE_REQUIRED_ROUTES)

    def test_release_tree_has_no_named_model_or_vendor_references(self):
        prohibited=("chat"+"gpt","clau"+"de","gem"+"ini","copi"+"lot","open"+"ai")
        hits=[]
        for path in ROOT.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix==".pyc":
                continue
            try: text=path.read_text(encoding="utf-8").casefold()
            except Exception: continue
            for token in prohibited:
                if token in text: hits.append((str(path.relative_to(ROOT)),token))
        self.assertEqual([],hits)


if __name__ == "__main__":
    unittest.main()
