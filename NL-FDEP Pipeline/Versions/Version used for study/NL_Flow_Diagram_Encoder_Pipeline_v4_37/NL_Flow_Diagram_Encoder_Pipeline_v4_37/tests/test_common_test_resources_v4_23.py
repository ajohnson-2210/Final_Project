import json
import tempfile
import unittest
from pathlib import Path

from common_test_resources import DEFAULT_COMMON_TESTS_ROOT, find_common_test_file, validate_common_test_pack
from pseudocode_profiles import PseudocodeProfile
from study_batch import StudyBatchProcessor
from study_provenance import validate_baseline


class CommonTestResourcesV423Tests(unittest.TestCase):
    def _complete_pack(self, root: Path) -> None:
        # 6 suites x 4 tests + 44 suites x 3 tests = 156 tests.
        for algorithm_id in range(1, 51):
            folder = root / "python" / f"Algorithm - {algorithm_id}"
            folder.mkdir(parents=True, exist_ok=True)
            count = 4 if algorithm_id <= 6 else 3
            tests = [
                {
                    "name": f"case-{index}",
                    "standard_input": [],
                    "category": "NORMAL",
                    "criteria_links": ["P2", "P4"],
                }
                for index in range(count)
            ]
            (folder / f"Algorithm {algorithm_id} Tests.json").write_text(
                json.dumps({
                    "test_design_version": "1.1",
                    "test_spec_schema_version": "1.2",
                    "algorithm_id": algorithm_id,
                    "evidence_adequacy": "LIMITED",
                    "tests": tests,
                }),
                encoding="utf-8",
            )


    def test_distributed_pack_is_complete_and_declares_v11_g2_metadata(self):
        status = validate_common_test_pack()
        self.assertTrue(status.complete)
        self.assertEqual(50, status.suite_count)
        self.assertEqual(156, status.test_count)
        required = {
            "evidence_summary", "coverage_dimensions", "coverage_basis",
            "interpretation_guidance", "coverage_limitations",
        }
        for algorithm_id in range(1, 51):
            path = find_common_test_file(algorithm_id, DEFAULT_COMMON_TESTS_ROOT)
            self.assertIsNotNone(path)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("1.4.2", data.get("test_design_version"))
            self.assertEqual("1.6", data.get("test_spec_schema_version"))
            self.assertTrue(required.issubset(data))
            self.assertEqual(6, len(data["coverage_dimensions"]))

    def test_complete_pack_requires_50_suites_and_156_tests(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._complete_pack(root)
            status = validate_common_test_pack(root)
            self.assertTrue(status.complete)
            self.assertEqual(50, status.suite_count)
            self.assertEqual(156, status.test_count)
            self.assertEqual([], status.missing_algorithm_ids)

    def test_packaged_test_precedes_baseline_local_test(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packaged = root / "pack"
            baseline_algorithm = root / "baseline" / "python" / "Algorithm - 1"
            packaged.mkdir(parents=True)
            baseline_algorithm.mkdir(parents=True)
            packaged_file = packaged / "Algorithm 1 Tests.json"
            local_file = baseline_algorithm / "Algorithm 1 Tests.json"
            packaged_file.write_text(json.dumps({"algorithm_id": 1, "tests": []}), encoding="utf-8")
            local_file.write_text(json.dumps({"algorithm_id": 1, "tests": [{"name": "local"}]}), encoding="utf-8")
            processor = StudyBatchProcessor(common_tests_root=packaged)
            self.assertEqual(packaged_file, processor._tests_for_algorithm(1, baseline_algorithm))

    def test_baseline_preflight_accepts_packaged_test_without_physical_merge(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "Baseline"
            pseudo = baseline / "pseudocode" / "Algorithm - 1"
            python = baseline / "python" / "Algorithm - 1"
            pack = root / "common"
            pseudo.mkdir(parents=True)
            python.mkdir(parents=True)
            pack.mkdir(parents=True)
            (pseudo / "Algorithm 1 Pseudocode.txt").write_text('OUTPUT STRING("ok")\n', encoding="utf-8")
            (python / "Algorithm 1 Baseline Python code.txt").write_text('print("ok")\n', encoding="utf-8")
            test_path = pack / "Algorithm 1 Tests.json"
            test_path.write_text(json.dumps({
                "test_spec_schema_version": "1.2",
                "algorithm_id": 1,
                "tests": [{"name": "normal", "standard_input": []}],
            }), encoding="utf-8")
            report = validate_baseline(baseline, expected_ids=[1], common_tests_root=pack)
            self.assertEqual(0, report["issue_count"])
            self.assertEqual("BUNDLED_COMMON_TESTS_V1_1", report["algorithms"][0]["tests_source"])
            self.assertEqual(str(test_path.resolve()), report["algorithms"][0]["tests_file"])

    def test_baseline_processing_uses_packaged_test_without_writing_to_baseline_python_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "Baseline"
            pseudo = baseline / "pseudocode" / "Algorithm - 1"
            python = baseline / "python" / "Algorithm - 1"
            pack = root / "common"
            pseudo.mkdir(parents=True)
            python.mkdir(parents=True)
            pack.mkdir(parents=True)
            (pseudo / "Algorithm 1 Pseudocode.txt").write_text('OUTPUT STRING("ok")\n', encoding="utf-8")
            (python / "Algorithm 1 Baseline Python code.txt").write_text('print("ok")\n', encoding="utf-8")
            packaged_test = pack / "Algorithm 1 Tests.json"
            packaged_test.write_text(json.dumps({
                "test_spec_schema_version": "1.2",
                "algorithm_id": 1,
                "evidence_adequacy": "LIMITED",
                "evidence_summary": "One normal-path test.",
                "coverage_dimensions": {"normal_path": "COVERED"},
                "coverage_basis": "Packaged common-test resource.",
                "interpretation_guidance": "Interpret for this scenario only.",
                "coverage_limitations": [],
                "tests": [{"name": "normal", "standard_input": [], "category": "NORMAL"}],
            }), encoding="utf-8")
            result = StudyBatchProcessor(common_tests_root=pack).process_baseline(
                baseline,
                profile=PseudocodeProfile.AJ_DIALECT_STRICT,
            )
            self.assertEqual({"SUCCESS": 1}, result["report"]["pipeline_status_counts"])
            self.assertFalse((python / "Algorithm 1 Tests.json").exists())
            manifest = json.loads((pseudo / "pipeline_artifacts" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(str(packaged_test.resolve()), manifest["tests_file"])


if __name__ == "__main__":
    unittest.main()
