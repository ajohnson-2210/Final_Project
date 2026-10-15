import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from aj_test_harness import AJTestHarness, TestCase
from drawio_importer import DrawIOFlowImporter, DrawIOImportError
from flow_input_pipeline import DrawIOFlowInputPipeline


VALID_DRAWIO = """<?xml version="1.0" encoding="UTF-8"?>
<mxfile>
  <diagram>
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="start" value="Start" vertex="1" parent="1">
          <mxGeometry x="100" y="20" width="120" height="50" as="geometry"/>
        </mxCell>
        <mxCell id="assign" value="AJ: total &lt;- INTEGER(0)" vertex="1" parent="1">
          <mxGeometry x="100" y="100" width="180" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="output" value="AJ: OUTPUT total" vertex="1" parent="1">
          <mxGeometry x="100" y="190" width="180" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="end" value="End" vertex="1" parent="1">
          <mxGeometry x="100" y="280" width="120" height="50" as="geometry"/>
        </mxCell>
        <mxCell id="e1" edge="1" source="start" target="assign" parent="1"/>
        <mxCell id="e2" edge="1" source="assign" target="output" parent="1"/>
        <mxCell id="e3" edge="1" source="output" target="end" parent="1"/>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
"""


class DrawIOInputTests(unittest.TestCase):

    def test_drawio_import_reconstructs_aj_pseudocode(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "linear.drawio"
            input_path.write_text(VALID_DRAWIO, encoding="utf-8")
            result = DrawIOFlowImporter().import_file(input_path)

        self.assertEqual(result.pseudocode, "total <- INTEGER(0)\nOUTPUT total")

    def test_drawio_route_generates_and_executes_python(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "linear.drawio"
            input_path.write_text(VALID_DRAWIO, encoding="utf-8")
            result = DrawIOFlowInputPipeline().run(
                input_path=input_path,
                output_directory=root / "output",
                test_cases=[TestCase("Draw.io total", expected_output=["0"])],
                open_visualisations=False,
            )

            generated_source = Path(
                result.output_files["generated_python"]
            ).read_text(encoding="utf-8")

        self.assertTrue(result.success, result.to_json())
        self.assertIn("total = 0", generated_source)
        self.assertIn("print(total)", generated_source)
        self.assertEqual(result.stages[0].name, "DRAWIO_IMPORT")


    def test_overlaid_start_and_end_text_are_associated_with_shapes(self):
        overlaid = VALID_DRAWIO.replace(
            '<mxCell id="start" value="Start" vertex="1" parent="1">',
            '<mxCell id="start" value="" style="rounded=1;" vertex="1" parent="1">',
        ).replace(
            '<mxCell id="end" value="End" vertex="1" parent="1">',
            '<mxCell id="end" value="" style="rounded=1;" vertex="1" parent="1">',
        ).replace(
            '<mxCell id="e1" edge="1" source="start" target="assign" parent="1"/>',
            '<mxCell id="start_label" value="Start" '
            'style="text;strokeColor=none;fillColor=none;" vertex="1" parent="1">'
            '<mxGeometry x="130" y="30" width="60" height="30" as="geometry"/>'
            '</mxCell>'
            '<mxCell id="end_label" value="End" '
            'style="text;strokeColor=none;fillColor=none;" vertex="1" parent="1">'
            '<mxGeometry x="130" y="290" width="60" height="30" as="geometry"/>'
            '</mxCell>'
            '<mxCell id="e1" edge="1" source="start" target="assign" parent="1"/>',
        )

        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "overlaid_labels.drawio"
            input_path.write_text(overlaid, encoding="utf-8")
            result = DrawIOFlowImporter().import_file(input_path)

        self.assertEqual(
            result.pseudocode,
            "total <- INTEGER(0)\nOUTPUT total",
        )

    def test_branching_diagram_generates_state_machine_flow(self):
        branching = VALID_DRAWIO.replace(
            '<mxCell id="assign" value="AJ: total &lt;- INTEGER(0)" vertex="1" parent="1">',
            '<mxCell id="assign" value="total == 0" style="rhombus;" vertex="1" parent="1">',
        ).replace(
            '<mxCell id="e2" edge="1" source="assign" target="output" parent="1"/>',
            '<mxCell id="e2" value="Yes" edge="1" source="assign" target="output" parent="1"/>'
            '<mxCell id="e4" value="No" edge="1" source="assign" target="end" parent="1"/>',
        )

        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "branch.drawio"
            input_path.write_text(branching, encoding="utf-8")
            result = DrawIOFlowImporter().import_file(input_path)

        self.assertFalse(result.is_linear)
        self.assertEqual(
            result.flow_document["structured_program"]["execution_model"],
            "STATE_MACHINE",
        )

    def test_uploaded_tic_tac_toe_diagram_is_accepted_and_compiles(self):
        project_root = Path(__file__).resolve().parent.parent
        input_path = project_root / "examples" / "tic_tac_toe" / "tic_tac_toe.drawio"

        with tempfile.TemporaryDirectory() as directory:
            result = DrawIOFlowInputPipeline().run(
                input_path=input_path,
                output_directory=Path(directory) / "output",
                test_cases=[],
                open_visualisations=False,
            )
            generated_source = Path(
                result.output_files["generated_python"]
            ).read_text(encoding="utf-8")

        self.assertTrue(result.success, result.to_json())
        self.assertNotIn("while current_node", generated_source)
        self.assertIn("while turn_counter < 9", generated_source)
        self.assertIn("winning_lines = [", generated_source)
        self.assertIn("Player {player_number} is declared the winner", generated_source)
        self.assertLess(len(generated_source.splitlines()), 80)
        self.assertEqual(
            result.input_metadata["execution_model"],
            "STRUCTURED_GRAPH_OPTIMISATION",
        )

    def test_flow_input_outputs_ast_and_adjacency_without_duplicate_flow_visualisation(self):
        project_root = Path(__file__).resolve().parent.parent
        input_path = project_root / "examples" / "tic_tac_toe" / "tic_tac_toe.drawio"

        with tempfile.TemporaryDirectory() as directory:
            result = DrawIOFlowInputPipeline().run(
                input_path=input_path,
                output_directory=Path(directory) / "output",
                test_cases=[],
                open_visualisations=False,
            )

            ast_document = Path(result.output_files["ast"]).read_text(
                encoding="utf-8"
            )
            adjacency_document = Path(
                result.output_files["ast_adjacency_list"]
            ).read_text(encoding="utf-8")

        self.assertTrue(result.success, result.to_json())
        self.assertIn('"node_type": "Module"', ast_document)
        self.assertIn('"root_id": "P1"', adjacency_document)
        self.assertIn("ast_visualisation", result.output_files)
        self.assertNotIn("flow_visualisation", result.output_files)
        self.assertNotIn("flow_diagram", result.output_files)

    def test_ast_visualisation_includes_zoom_controls_and_readable_start_view(self):
        project_root = Path(__file__).resolve().parent.parent
        input_path = project_root / "examples" / "tic_tac_toe" / "tic_tac_toe.drawio"

        with tempfile.TemporaryDirectory() as directory:
            result = DrawIOFlowInputPipeline().run(
                input_path=input_path,
                output_directory=Path(directory) / "output",
                test_cases=[],
                open_visualisations=False,
            )
            html = Path(result.output_files["ast_visualisation"]).read_text(
                encoding="utf-8"
            )

        self.assertIn('id="zoom-in"', html)
        self.assertIn('id="zoom-out"', html)
        self.assertIn('id="reset-view"', html)
        self.assertIn('const INITIAL_SCALE = 1.15;', html)
        self.assertIn('requestAnimationFrame(resetView);', html)

    def test_uploaded_tic_tac_toe_program_declares_player_one_winner(self):
        project_root = Path(__file__).resolve().parent.parent
        input_path = project_root / "examples" / "tic_tac_toe" / "tic_tac_toe.drawio"

        with tempfile.TemporaryDirectory() as directory:
            output_directory = Path(directory) / "output"
            result = DrawIOFlowInputPipeline().run(
                input_path=input_path,
                output_directory=output_directory,
                test_cases=[],
                open_visualisations=False,
            )
            generated_program = Path(result.output_files["generated_python"])
            report = AJTestHarness().run(
                generated_program,
                [
                    TestCase(
                        "Tic tac toe winner",
                        standard_input=["0", "3", "1", "4", "2"],
                        expected_output=[],
                    )
                ],
            )
            case = report.results[0]

        self.assertEqual(case.return_code, 0, case.standard_error)
        output_text = "\n".join(case.actual_output)
        self.assertIn("Player 1 is declared the winner", output_text)
        self.assertNotIn("safety step limit", output_text)

    def test_uploaded_tic_tac_toe_program_declares_draw(self):
        project_root = Path(__file__).resolve().parent.parent
        input_path = project_root / "examples" / "tic_tac_toe" / "tic_tac_toe.drawio"

        with tempfile.TemporaryDirectory() as directory:
            output_directory = Path(directory) / "output"
            result = DrawIOFlowInputPipeline().run(
                input_path=input_path,
                output_directory=output_directory,
                test_cases=[],
                open_visualisations=False,
            )
            generated_program = Path(result.output_files["generated_python"])
            report = AJTestHarness().run(
                generated_program,
                [
                    TestCase(
                        "Tic tac toe draw",
                        standard_input=["0", "1", "2", "4", "3", "5", "7", "6", "8"],
                        expected_output=[],
                    )
                ],
            )
            case = report.results[0]

        self.assertEqual(case.return_code, 0, case.standard_error)
        self.assertIn("Game is declared a draw", "\n".join(case.actual_output))


if __name__ == "__main__":
    unittest.main()
