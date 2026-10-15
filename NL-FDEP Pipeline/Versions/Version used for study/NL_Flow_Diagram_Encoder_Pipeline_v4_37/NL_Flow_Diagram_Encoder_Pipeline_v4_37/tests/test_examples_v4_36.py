import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
for directory in [
    "parser components",
    "compiler components",
    "flow diagram components",
    "pipeline components",
    "test components",
    "study components",
]:
    path = str(ROOT / directory)
    if path not in sys.path:
        sys.path.insert(0, path)

from common_test_resources import TEST_DESIGN_VERSION, TEST_SPEC_SCHEMA_VERSION
from nl_flow_pipeline import NLFlowDiagramEncoderPipeline
from flow_input_pipeline import DrawIOFlowInputPipeline
from aj_test_harness import TestCase
from pseudocode_profiles import PseudocodeProfile
from study_rubric import PIPELINE_VERSION


def test_release_version_is_436():
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "4.37"
    assert PIPELINE_VERSION == "4.37"


def test_study_template_matches_active_static_semantic_methodology():
    data = json.loads((ROOT / "docs" / "study_tests_template.json").read_text(encoding="utf-8"))
    assert data["test_spec_schema_version"] == TEST_SPEC_SCHEMA_VERSION == "1.6"
    assert data["test_design_version"] == TEST_DESIGN_VERSION == "1.4.2"
    assert data["oracle_policy"] == "STATIC_PREEXPERIMENT_EXPECTATIONS"
    assert data["semantic_contract"]["runtime_oracle_prohibited"] is True
    assert data["tests"][0]["score_stream"] == "CORE_BEHAVIOURAL"


def test_primary_example_matches_current_pipeline(tmp_path):
    examples = ROOT / "examples"
    result = NLFlowDiagramEncoderPipeline().run(
        (examples / "source_pseudocode.aj").read_text(encoding="utf-8"),
        tmp_path,
        [],
        False,
        PseudocodeProfile.AJ_DIALECT_STRICT,
    )
    assert result.success is True
    def canonical_ast(document):
        nodes = document["nodes"]
        adjacency = document["adjacency"]
        order = []
        seen = set()
        def walk(node_id):
            if node_id in seen:
                return
            seen.add(node_id)
            order.append(node_id)
            for child in adjacency.get(node_id, []):
                walk(child)
        walk(document["root_id"])
        index = {node_id: i for i, node_id in enumerate(order)}
        return [
            {
                "kind": nodes[node_id]["kind"],
                "line": nodes[node_id]["line"],
                "attributes": nodes[node_id]["attributes"],
                "children": [index[child] for child in adjacency.get(node_id, [])],
            }
            for node_id in order
        ]

    assert canonical_ast(json.loads((tmp_path / "ast.json").read_text(encoding="utf-8"))) == canonical_ast(
        json.loads((examples / "ast.json").read_text(encoding="utf-8"))
    )
    assert json.loads((tmp_path / "flow_diagram.json").read_text(encoding="utf-8")) == json.loads(
        (examples / "flow_diagram.json").read_text(encoding="utf-8")
    )
    assert (tmp_path / "generated_program.py").read_text(encoding="utf-8") == (
        examples / "generated_program.py"
    ).read_text(encoding="utf-8")


def test_examples_do_not_teach_retired_oracle_or_dialect_wording():
    template = (ROOT / "docs" / "study_tests_template.json").read_text(encoding="utf-8")
    example_summary = (ROOT / "examples" / "run_summary.txt").read_text(encoding="utf-8")
    tic_summary = (ROOT / "examples" / "tic_tac_toe" / "run_summary.txt").read_text(encoding="utf-8")
    assert "TRUSTED_BASELINE_REFERENCE" not in template
    assert "DIALECT V1.0" not in example_summary
    assert "v4.37" in example_summary
    assert "v4.37" in tic_summary

    legacy_example_names = {
        "ast_output.json",
        "example.aj",
        "example_ast.json",
        "example_compilation_report.json",
        "example_flow_diagram.drawio",
        "example_flow_diagram.html",
        "example_flow_diagram.json",
        "example_generated_program.py",
        "example_pipeline_report.json",
        "example_pseudocode_processing_report.json",
        "example_report.json",
        "example_run.txt",
        "pycharm_example_output.txt",
        "study_tests_template.json",
        "tic_tac_toe.drawio",
    }
    packaged_root_names = {path.name for path in (ROOT / "examples").iterdir() if path.is_file()}
    assert packaged_root_names.isdisjoint(legacy_example_names)


def test_tic_tac_toe_presentation_example_matches_drawio_pipeline(tmp_path):
    example = ROOT / "examples" / "tic_tac_toe"
    spec = json.loads((example / "test_cases.json").read_text(encoding="utf-8"))
    cases = [
        TestCase(
            name=item["name"],
            standard_input=item.get("standard_input", []),
            expected_output=item.get("expected_output"),
            expected_return_code=item.get("expected_return_code"),
            category=item.get("category", "DEMONSTRATION"),
        )
        for item in spec["tests"]
    ]
    result = DrawIOFlowInputPipeline().run(
        input_path=example / "tic_tac_toe.drawio",
        output_directory=tmp_path,
        test_cases=cases,
        open_visualisations=False,
    )
    assert result.success is True
    assert [stage.name for stage in result.stages] == [
        "DRAWIO_IMPORT",
        "DRAWIO_GRAPH_VALIDATION",
        "PYTHON_AST_GENERATION",
        "FLOW_DIAGRAM_TO_PYTHON",
        "BEHAVIOURAL_TESTING",
    ]
    assert all(stage.status == "SUCCESS" for stage in result.stages)
    assert result.test_report is not None
    assert result.test_report.passed_tests == 2
    assert (tmp_path / "generated_program.py").read_text(encoding="utf-8") == (
        example / "generated_program.py"
    ).read_text(encoding="utf-8")
