import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from input_selection import InputRoute, InputSelectionDialog
from pycharm_runner import run_selected_pipeline
from pseudocode_profiles import PseudocodeProfile


class InputSelectionTests(unittest.TestCase):

    def test_pseudocode_route_uses_pseudocode_pipeline(self):
        expected_result = object()

        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "algorithm.aj"
            input_path.write_text("OUTPUT INTEGER(1)", encoding="utf-8")

            with patch(
                "pycharm_runner.run_pseudocode_pipeline",
                return_value=expected_result,
            ) as mocked_pipeline:
                result = run_selected_pipeline(
                    route=InputRoute.PSEUDOCODE,
                    input_path=input_path,
                    pseudocode_profile=PseudocodeProfile.GENERAL_NO_CONVERSION,
                )

        self.assertIs(result, expected_result)
        mocked_pipeline.assert_called_once_with(
            input_path=input_path,
            pseudocode_profile=PseudocodeProfile.GENERAL_NO_CONVERSION,
        )

    def test_flow_diagram_route_uses_drawio_pipeline(self):
        expected_result = object()
        input_path = Path("algorithm.drawio")

        with patch(
            "pycharm_runner.run_flow_diagram_pipeline",
            return_value=expected_result,
        ) as mocked_pipeline:
            result = run_selected_pipeline(
                route=InputRoute.FLOW_DIAGRAM,
                input_path=input_path,
            )

        self.assertIs(result, expected_result)
        mocked_pipeline.assert_called_once_with(
            input_path=input_path,
        )

    def test_file_filters_match_selected_input_route(self):
        dialog = InputSelectionDialog()

        pseudocode_filters = dialog._file_types(
            InputRoute.PSEUDOCODE
        )
        flow_filters = dialog._file_types(
            InputRoute.FLOW_DIAGRAM
        )

        self.assertIn(
            ("AJ pseudocode", "*.aj *.txt"),
            pseudocode_filters,
        )
        self.assertIn(
            ("draw.io files", "*.drawio *.xml *.svg"),
            flow_filters,
        )


if __name__ == "__main__":
    unittest.main()
