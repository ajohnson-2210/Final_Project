import tempfile
import unittest
from pathlib import Path

from pycharm_runner import _normalise_llm_results_directory, select_llm_results_directory


def _make_algorithm_folder(parent: Path, algorithm_id: int = 1) -> None:
    folder = parent / f"Algorithm - {algorithm_id}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"Algorithm {algorithm_id} Pseudocode.txt").write_text("OUTPUT STRING(\"ok\")\n", encoding="utf-8")


class _SelectionDialog:
    def __init__(self, selections):
        self.selections = [Path(value) for value in selections]
        self.infos = []
        self.errors = []

    def show_info(self, title, message):
        self.infos.append((title, message))

    def show_error(self, title, message):
        self.errors.append((title, message))

    def select_file(self, route):
        if not self.selections:
            raise AssertionError("Unexpected additional selection request")
        return self.selections.pop(0)


class RunnerLlmFolderSelectionHotfixTests(unittest.TestCase):
    def test_direct_algorithm_folder_layout_is_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "Experiment"
            root.mkdir()
            _make_algorithm_folder(root)
            self.assertEqual(root, _normalise_llm_results_directory(root))

    def test_parent_with_results_child_is_normalised(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "Experiment"
            results = root / "results"
            results.mkdir(parents=True)
            _make_algorithm_folder(results)
            self.assertEqual(results, _normalise_llm_results_directory(root))

    def test_baseline_selection_is_rejected_then_llm_parent_is_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            baseline = base / "Baselines"
            baseline.mkdir()
            llm_root = base / "Model A"
            results = llm_root / "results"
            results.mkdir(parents=True)
            _make_algorithm_folder(results)

            dialog = _SelectionDialog([baseline, llm_root])
            selected = select_llm_results_directory(dialog, baseline)

            self.assertEqual(results, selected)
            self.assertEqual(1, len(dialog.infos))
            self.assertEqual(1, len(dialog.errors))
            self.assertIn("cannot also be used", dialog.errors[0][1])


    def test_baseline_independent_llm_selection_accepts_valid_folder(self):
        with tempfile.TemporaryDirectory() as temp:
            llm = Path(temp) / "Valid"
            llm.mkdir()
            _make_algorithm_folder(llm)

            dialog = _SelectionDialog([llm])
            selected = select_llm_results_directory(dialog, None)

            self.assertEqual(llm, selected)
            self.assertEqual(1, len(dialog.infos))
            self.assertEqual("Select LLM results dataset", dialog.infos[0][0])
            self.assertEqual([], dialog.errors)

    def test_unrecognised_folder_is_reprompted(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            baseline = base / "Baselines"
            baseline.mkdir()
            empty = base / "Empty"
            empty.mkdir()
            llm = base / "Valid"
            llm.mkdir()
            _make_algorithm_folder(llm)

            dialog = _SelectionDialog([empty, llm])
            selected = select_llm_results_directory(dialog, baseline)

            self.assertEqual(llm, selected)
            self.assertEqual(1, len(dialog.errors))
            self.assertIn("No 'Algorithm - n' folders", dialog.errors[0][1])


if __name__ == "__main__":
    unittest.main()
