"""Second controlled input route for draw.io flow diagrams."""

from __future__ import annotations

from pathlib import Path
import time
import json

from aj_python_compiler import AJPythonCompiler
from aj_test_harness import AJTestHarness, TestCase
from drawio_importer import DrawIOFlowImporter
from flow_diagram import FlowDiagram
from nl_flow_pipeline import NLFlowDiagramEncoderPipeline, PipelineResult, PipelineStage
from ast_visualizer import ASTHtmlVisualizer
from python_ast import PythonASTBuilder


class DrawIOFlowInputPipeline:
    """Imports a draw.io file and then reuses the canonical AJ pipeline."""

    def __init__(self) -> None:
        self.importer = DrawIOFlowImporter()
        self.canonical_pipeline = NLFlowDiagramEncoderPipeline()

    def run(
        self,
        input_path: Path,
        output_directory: Path,
        test_cases: list[TestCase],
        open_visualisations: bool = False,
    ) -> PipelineResult:
        import_started = time.perf_counter()

        try:
            import_result = self.importer.import_file(input_path)
        except Exception as error:
            return PipelineResult(
                success=False,
                status="FAILURE",
                stages=[
                    PipelineStage(
                        name="DRAWIO_IMPORT",
                        status="FAILURE",
                        message=str(error),
                        duration_ms=round(
                            (time.perf_counter() - import_started) * 1000,
                            3,
                        ),
                    )
                ],
                output_files={},
                error=str(error),
            )

        output_directory.mkdir(parents=True, exist_ok=True)

        if import_result.is_linear:
            imported_source_path = output_directory / "imported_flow_pseudocode.aj"
            imported_source_path.write_text(import_result.pseudocode, encoding="utf-8")

            result = self.canonical_pipeline.run(
                pseudocode=import_result.pseudocode,
                output_directory=output_directory,
                test_cases=test_cases,
                open_visualisations=open_visualisations,
            )
            result.output_files["imported_pseudocode"] = str(
                imported_source_path.resolve()
            )
        else:
            result = self._run_graph_pipeline(
                flow_document=import_result.flow_document,
                output_directory=output_directory,
                test_cases=test_cases,
                open_visualisations=open_visualisations,
            )

        import_stage = PipelineStage(
            name="DRAWIO_IMPORT",
            status="SUCCESS",
            message=(
                f"Imported {import_result.shape_count} shapes and "
                f"{import_result.connector_count} connectors."
            ),
            duration_ms=round(
                (time.perf_counter() - import_started) * 1000,
                3,
            ),
        )

        result.stages.insert(0, import_stage)
        pipeline_report_path = output_directory / "pipeline_report.json"
        pipeline_report_path.write_text(result.to_json(), encoding="utf-8")

        return result
    def _run_graph_pipeline(
        self,
        flow_document: dict | None,
        output_directory: Path,
        test_cases: list[TestCase],
        open_visualisations: bool,
    ) -> PipelineResult:
        """Compiles a general draw.io control-flow graph as a state machine."""

        if flow_document is None:
            raise ValueError("Draw.io graph document was not generated.")

        stages: list[PipelineStage] = []
        output_files: dict[str, str] = {}

        try:
            flow_diagram = FlowDiagram.from_dict(flow_document)
            stages.append(
                PipelineStage(
                    name="DRAWIO_GRAPH_VALIDATION",
                    status="SUCCESS",
                    message="Imported flow graph validated for compilation.",
                    duration_ms=0.0,
                )
            )

            compilation_result = AJPythonCompiler().compile(flow_diagram)
            generated_program_path = output_directory / "generated_program.py"
            generated_program_path.write_text(
                compilation_result.source_code,
                encoding="utf-8",
            )
            output_files["generated_python"] = str(
                generated_program_path.resolve()
            )

            python_ast_result = PythonASTBuilder().build(
                compilation_result.source_code
            )
            ast_path = output_directory / "ast.json"
            ast_path.write_text(
                json.dumps(python_ast_result.tree_document, indent=2),
                encoding="utf-8",
            )
            output_files["ast"] = str(ast_path.resolve())

            adjacency_path = output_directory / "ast_adjacency_list.json"
            adjacency_path.write_text(
                python_ast_result.adjacency_list.to_json(),
                encoding="utf-8",
            )
            output_files["ast_adjacency_list"] = str(
                adjacency_path.resolve()
            )

            ast_visualisation_path = ASTHtmlVisualizer(
                title="Generated Python AST Visualisation"
            ).generate(
                python_ast_result.adjacency_list,
                output_path=output_directory / "ast_visualisation.html",
                open_browser=open_visualisations,
            )
            output_files["ast_visualisation"] = str(
                ast_visualisation_path.resolve()
            )
            stages.append(
                PipelineStage(
                    name="PYTHON_AST_GENERATION",
                    status="SUCCESS",
                    message=(
                        "Generated Python AST and adjacency list created."
                    ),
                    duration_ms=0.0,
                )
            )
            stages.append(
                PipelineStage(
                    name="FLOW_DIAGRAM_TO_PYTHON",
                    status="SUCCESS",
                    message=compilation_result.message,
                    duration_ms=0.0,
                )
            )

            compilation_report_path = output_directory / "compilation_report.json"
            compilation_report_path.write_text(
                json.dumps(
                    {
                        "success": compilation_result.success,
                        "message": compilation_result.message,
                        "source_file": str(generated_program_path.resolve()),
                        "execution_model": compilation_result.execution_model,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            output_files["compilation_report"] = str(
                compilation_report_path.resolve()
            )

            if test_cases:
                test_report = AJTestHarness().run(
                    program_path=generated_program_path,
                    test_cases=test_cases,
                )
                test_report_path = output_directory / "test_report.json"
                test_report_path.write_text(test_report.to_json(), encoding="utf-8")
                output_files["test_report"] = str(test_report_path.resolve())
                stages.append(
                    PipelineStage(
                        name="BEHAVIOURAL_TESTING",
                        status="SUCCESS" if test_report.success else "FAILURE",
                        message=(
                            f"{test_report.passed_tests}/"
                            f"{len(test_report.results)} tests passed."
                        ),
                        duration_ms=0.0,
                    )
                )
                success = test_report.success
            else:
                test_report = None
                stages.append(
                    PipelineStage(
                        name="BEHAVIOURAL_TESTING",
                        status="SKIPPED",
                        message=(
                            "No behavioural oracle was supplied; compilation and "
                            "Python syntax validation completed."
                        ),
                        duration_ms=0.0,
                    )
                )
                success = True

            return PipelineResult(
                success=success,
                status="SUCCESS" if success else "FAILURE",
                stages=stages,
                output_files=output_files,
                test_report=test_report,
                input_metadata={
                    "input_type": "FLOW_DIAGRAM",
                    "execution_model": compilation_result.execution_model,
                },
            )
        except Exception as error:
            stages.append(
                PipelineStage(
                    name="GRAPH_PIPELINE_FAILURE",
                    status="FAILURE",
                    message=str(error),
                    duration_ms=0.0,
                )
            )
            return PipelineResult(
                success=False,
                status="FAILURE",
                stages=stages,
                output_files=output_files,
                error=str(error),
                input_metadata={
                    "input_type": "FLOW_DIAGRAM",
                    "execution_model": "STATE_MACHINE",
                },
            )

