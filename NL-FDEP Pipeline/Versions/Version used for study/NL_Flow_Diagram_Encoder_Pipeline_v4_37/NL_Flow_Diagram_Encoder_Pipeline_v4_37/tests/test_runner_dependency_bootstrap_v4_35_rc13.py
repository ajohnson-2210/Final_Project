import unittest
from unittest.mock import patch

import pycharm_runner


class _Dialog:
    def __init__(self, answer=True):
        self.answer = answer
        self.questions = []
        self.errors = []

    def ask_yes_no(self, title, message):
        self.questions.append((title, message))
        return self.answer

    def show_error(self, title, message):
        self.errors.append((title, message))


class RunnerDependencyBootstrapV435RC13Tests(unittest.TestCase):
    def test_satisfied_core_and_optional_requirements_do_not_run_pip(self):
        dialog = _Dialog()
        with patch("pycharm_runner._missing_requirement_distributions", return_value=[]), \
             patch("pycharm_runner._install_requirements_file") as install:
            self.assertTrue(pycharm_runner.ensure_runner_dependencies(dialog))
        install.assert_not_called()
        self.assertEqual([], dialog.questions)

    def test_missing_package_installs_core_then_optional_files(self):
        dialog = _Dialog(answer=True)
        with patch(
            "pycharm_runner._missing_requirement_distributions",
            side_effect=[["pytest"], ["matplotlib"], [], []],
        ), patch("pycharm_runner._install_requirements_file", return_value=True) as install:
            self.assertTrue(pycharm_runner.ensure_runner_dependencies(dialog))

        self.assertEqual(1, len(dialog.questions))
        self.assertEqual("Install NL-FDEP dependencies", dialog.questions[0][0])
        self.assertEqual(2, install.call_count)
        self.assertEqual("requirements.txt", install.call_args_list[0].args[0].name)
        self.assertEqual("requirements-optional.txt", install.call_args_list[1].args[0].name)

    def test_declined_installation_blocks_baseline_llm_dependency_gate(self):
        dialog = _Dialog(answer=False)
        with patch(
            "pycharm_runner._missing_requirement_distributions",
            side_effect=[[], ["matplotlib"]],
        ), patch("pycharm_runner._install_requirements_file") as install:
            self.assertFalse(pycharm_runner.ensure_runner_dependencies(dialog))
        install.assert_not_called()


if __name__ == "__main__":
    unittest.main()
