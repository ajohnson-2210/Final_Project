"""Application service for the complete pseudocode-only NL-FDEP pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import json
import time

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from aj_test_harness import AJTestHarness, TestCase, TestHarnessReport
from ast_visualizer import ASTHtmlVisualizer
from flow_diagram import FlowDiagramEncoder
from flow_diagram_visualizer import FlowDiagramVisualizer
from drawio_exporter import DrawIOFlowExporter
from pseudocode_profiles import (
    PseudocodeProfile,
    PseudocodeProfileProcessor,
)


@dataclass
class PipelineStage:
    """Records one high-level stage of the complete application pipeline."""

    name: str
    status: str
    message: str
    duration_ms: float


@dataclass
class PipelineResult:
    """Records the complete pipeline outcome and generated artefacts."""

    success: bool
    stages: list[PipelineStage]
    output_files: dict[str, str]
    test_report: TestHarnessReport | None = None
    error: str | None = None
    input_metadata: dict[str, Any] | None = None
    status: str = "SUCCESS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status,
            "stages": [asdict(stage) for stage in self.stages],
            "output_files": self.output_files,
            "test_report": (
                self.test_report.to_dict()
                if self.test_report is not None
                else None
            ),
            "error": self.error,
            "input_metadata": self.input_metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class NLFlowDiagramEncoderPipeline:
    """Runs pseudocode parsing, flow encoding, compilation, and testing."""

    def __init__(self) -> None:
        self.parser = AJParserFacade()
        self.flow_encoder = FlowDiagramEncoder()
        self.drawio_exporter = DrawIOFlowExporter()
        self.python_compiler = AJPythonCompiler()
        self.test_harness = AJTestHarness()
        self.profile_processor = PseudocodeProfileProcessor()

    def run(
        self,
        pseudocode: str,
        output_directory: Path,
        test_cases: list[TestCase],
        open_visualisations: bool = False,
        pseudocode_profile: PseudocodeProfile = PseudocodeProfile.AJ_DIALECT_STRICT,
    ) -> PipelineResult:
        output_directory.mkdir(parents=True, exist_ok=True)
        stages: list[PipelineStage] = []
        output_files: dict[str, str] = {}

        try:
            processing_start = time.perf_counter()
            processing_result = self.profile_processor.process(
                source=pseudocode,
                profile=pseudocode_profile,
            )
            processing_duration = (time.perf_counter() - processing_start) * 1000

            stages.append(
                PipelineStage(
                    "PSEUDOCODE_PROFILE_PROCESSING",
                    "SUCCESS",
                    (
                        f"Processed source using {pseudocode_profile.value}; "
                        f"{processing_result.transformation_count} transformation(s); "
                        f"{processing_result.header_lines_removed} header line(s) stripped."
                    ),
                    round(processing_duration, 3),
                )
            )

            normalisation_report_path = output_directory / "pseudocode_processing_report.json"
            normalisation_report_path.write_text(
                processing_result.to_json(),
                encoding="utf-8",
            )
            output_files["pseudocode_processing_report"] = str(
                normalisation_report_path.resolve()
            )

            processed_source_path = output_directory / "processed_pseudocode.aj"
            processed_source_path.write_text(
                processing_result.processed_source,
                encoding="utf-8",
            )
            output_files["processed_pseudocode"] = str(
                processed_source_path.resolve()
            )

            parse_start = time.perf_counter()
            parse_result = self.parser.parse(
                processing_result.processed_source
            )
            parse_duration = (time.perf_counter() - parse_start) * 1000

            if not parse_result.success or parse_result.ast is None:
                stages.append(
                    PipelineStage(
                        "PSEUDOCODE_TO_AST",
                        "FAILURE",
                        parse_result.error or "Pseudocode parsing failed.",
                        round(parse_duration, 3),
                    )
                )
                raise ValueError(parse_result.error or "Pseudocode parsing failed.")

            stages.append(
                PipelineStage(
                    "PSEUDOCODE_TO_AST",
                    "SUCCESS",
                    "Pseudocode parsed and validated.",
                    round(parse_duration, 3),
                )
            )

            ast_path = output_directory / "ast.json"
            ast_path.write_text(
                parse_result.adjacency_list.to_json(),
                encoding="utf-8",
            )
            output_files["ast"] = str(ast_path.resolve())

            parser_report_path = output_directory / "parser_report.json"
            parser_report_path.write_text(
                parse_result.report.to_json(),
                encoding="utf-8",
            )
            output_files["parser_report"] = str(parser_report_path.resolve())

            ast_html_path = ASTHtmlVisualizer().generate(
                parse_result.adjacency_list,
                output_path=output_directory / "ast_visualisation.html",
                open_browser=open_visualisations,
            )
            output_files["ast_visualisation"] = str(ast_html_path)

            flow_start = time.perf_counter()
            flow_diagram = self.flow_encoder.encode(parse_result.ast)
            flow_duration = (time.perf_counter() - flow_start) * 1000
            stages.append(
                PipelineStage(
                    "AST_TO_FLOW_DIAGRAM",
                    "SUCCESS",
                    "Machine-readable flow diagram generated.",
                    round(flow_duration, 3),
                )
            )

            flow_json_path = output_directory / "flow_diagram.json"
            flow_json_path.write_text(flow_diagram.to_json(), encoding="utf-8")
            output_files["flow_diagram"] = str(flow_json_path.resolve())

            flow_html_path = FlowDiagramVisualizer().generate(
                flow_diagram,
                output_path=output_directory / "flow_diagram.html",
                open_browser=open_visualisations,
            )
            output_files["flow_visualisation"] = str(flow_html_path)

            drawio_start = time.perf_counter()
            drawio_path = self.drawio_exporter.export(
                flow_diagram,
                output_path=output_directory / "flow_diagram.drawio",
            )
            drawio_duration = (time.perf_counter() - drawio_start) * 1000
            output_files["flow_diagram_drawio"] = str(drawio_path)
            stages.append(
                PipelineStage(
                    "FLOW_DIAGRAM_TO_DRAWIO",
                    "SUCCESS",
                    "Editable draw.io XML flow diagram generated.",
                    round(drawio_duration, 3),
                )
            )

            compilation_start = time.perf_counter()
            compilation_result = self.python_compiler.compile(flow_diagram)
            compilation_duration = (time.perf_counter() - compilation_start) * 1000
            compilation_status = "SUCCESS"
            if not compilation_result.success:
                compilation_status = (
                    "EXPECTED_FAILURE"
                    if compilation_result.message.startswith("Expected failure:")
                    else "FAILURE"
                )
            stages.append(
                PipelineStage(
                    "FLOW_DIAGRAM_TO_PYTHON",
                    compilation_status,
                    compilation_result.message,
                    round(compilation_duration, 3),
                )
            )

            generated_program_path = output_directory / "generated_program.py"
            if compilation_result.success:
                generated_program_path.write_text(
                    compilation_result.source_code,
                    encoding="utf-8",
                )
                output_files["generated_python"] = str(
                    generated_program_path.resolve()
                )

            compilation_report_path = output_directory / "compilation_report.json"
            compilation_report_path.write_text(
                json.dumps(
                    {
                        "success": compilation_result.success,
                        "status": compilation_status,
                        "message": compilation_result.message,
                        "source_file": (
                            str(generated_program_path.resolve())
                            if compilation_result.success
                            else None
                        ),
                        "execution_model": compilation_result.execution_model,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            output_files["compilation_report"] = str(
                compilation_report_path.resolve()
            )

            test_report = None
            if compilation_result.success and test_cases:
                testing_start = time.perf_counter()
                test_report = self.test_harness.run(
                    generated_program_path,
                    test_cases,
                )
                testing_duration = (time.perf_counter() - testing_start) * 1000
                testing_status = "SUCCESS" if test_report.success else "FAILURE"
                stages.append(
                    PipelineStage(
                        "BEHAVIOURAL_TESTING",
                        testing_status,
                        f"Passed {test_report.passed_tests} of {len(test_report.results)} tests.",
                        round(testing_duration, 3),
                    )
                )

                test_report_path = output_directory / "test_report.json"
                test_report_path.write_text(test_report.to_json(), encoding="utf-8")
                output_files["test_report"] = str(test_report_path.resolve())
            else:
                reason = (
                    "No behavioural tests were supplied."
                    if compilation_result.success
                    else "Python compilation did not produce an executable program."
                )
                stages.append(
                    PipelineStage(
                        "BEHAVIOURAL_TESTING",
                        "NOT_RUN",
                        reason,
                        0.0,
                    )
                )

            overall_status = compilation_status
            success = compilation_result.success
            if compilation_result.success and test_report is not None:
                success = test_report.success
                overall_status = "SUCCESS" if test_report.success else "FAILURE"

            result = PipelineResult(
                success=success,
                status=overall_status,
                stages=stages,
                output_files=output_files,
                test_report=test_report,
                input_metadata={
                    "input_type": "PSEUDOCODE",
                    "pseudocode_profile": pseudocode_profile.value,
                    "source_modified": processing_result.source_modified,
                    "transformation_count": processing_result.transformation_count,
                    "header_comment_removed": processing_result.header_comment_removed,
                    "header_lines_removed": processing_result.header_lines_removed,
                },
            )

        except Exception as error:
            if not stages or stages[-1].status not in {"FAILURE", "EXPECTED_FAILURE"}:
                stages.append(
                    PipelineStage(
                        "PIPELINE_FAILURE",
                        "FAILURE",
                        str(error),
                        0.0,
                    )
                )
            result = PipelineResult(
                success=False,
                status="FAILURE",
                stages=stages,
                output_files=output_files,
                error=str(error),
                input_metadata={
                    "input_type": "PSEUDOCODE",
                    "pseudocode_profile": pseudocode_profile.value,
                },
            )

        pipeline_report_path = output_directory / "pipeline_report.json"
        pipeline_report_path.write_text(result.to_json(), encoding="utf-8")
        result.output_files["pipeline_report"] = str(
            pipeline_report_path.resolve()
        )
        pipeline_report_path.write_text(result.to_json(), encoding="utf-8")

        return result
