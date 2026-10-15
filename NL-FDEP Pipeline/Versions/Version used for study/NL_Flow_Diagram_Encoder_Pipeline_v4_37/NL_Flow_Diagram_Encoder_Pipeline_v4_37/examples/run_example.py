"""Reproduce the presentation-ready NL-FDEP v4.37 single-program example."""

from __future__ import annotations

import json
from pathlib import Path
import sys

EXAMPLES = Path(__file__).resolve().parent
ROOT = EXAMPLES.parent
for component in (
    "parser components",
    "compiler components",
    "flow diagram components",
    "pipeline components",
    "study components",
):
    path = str(ROOT / component)
    if path not in sys.path:
        sys.path.insert(0, path)

from aj_test_harness import TestCase
from nl_flow_pipeline import NLFlowDiagramEncoderPipeline
from pseudocode_profiles import PseudocodeProfile


def _portable_path(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        path = Path(value).resolve()
        relative = path.relative_to(ROOT.resolve())
    except (OSError, ValueError):
        return value
    return relative.as_posix()


def _normalise_packaged_paths() -> None:
    """Normalise run-local absolute paths after generation for ZIP portability."""
    pipeline_path = EXAMPLES / "pipeline_report.json"
    pipeline = json.loads(pipeline_path.read_text(encoding="utf-8"))
    pipeline["output_files"] = {
        key: _portable_path(value) for key, value in pipeline["output_files"].items()
    }
    if pipeline.get("test_report"):
        pipeline["test_report"]["program_path"] = _portable_path(
            pipeline["test_report"].get("program_path")
        )
    pipeline_path.write_text(json.dumps(pipeline, indent=2) + "\n", encoding="utf-8")

    compilation_path = EXAMPLES / "compilation_report.json"
    compilation = json.loads(compilation_path.read_text(encoding="utf-8"))
    compilation["source_file"] = _portable_path(compilation.get("source_file"))
    compilation_path.write_text(json.dumps(compilation, indent=2) + "\n", encoding="utf-8")

    tests_path = EXAMPLES / "test_report.json"
    tests = json.loads(tests_path.read_text(encoding="utf-8"))
    tests["program_path"] = _portable_path(tests.get("program_path"))
    tests_path.write_text(json.dumps(tests, indent=2) + "\n", encoding="utf-8")


def _write_summary() -> None:
    pipeline = json.loads((EXAMPLES / "pipeline_report.json").read_text(encoding="utf-8"))
    tests = json.loads((EXAMPLES / "test_report.json").read_text(encoding="utf-8"))
    test_spec = json.loads((EXAMPLES / "test_cases.json").read_text(encoding="utf-8"))
    test_inputs = {item["name"]: item.get("standard_input", []) for item in test_spec["tests"]}
    source = (EXAMPLES / "source_pseudocode.aj").read_text(encoding="utf-8").strip()
    generated = (EXAMPLES / "generated_program.py").read_text(encoding="utf-8").strip()

    lines = [
        "NL-FDEP v4.37 — SINGLE-PROGRAM END-TO-END EXAMPLE",
        "=" * 58,
        "",
        "PURPOSE",
        "A presentation-ready, non-batch run of NLFlowDiagramEncoderPipeline.",
        "The same source is processed through every computational stage and then",
        "executed against four behavioural demonstration cases.",
        "",
        "SOURCE PSEUDOCODE",
        "",
        source,
        "",
        "PIPELINE STAGES",
        "",
    ]
    for stage in pipeline["stages"]:
        lines.append(
            f"[{stage['status']}] {stage['name']:<34} "
            f"{stage['duration_ms']:>9.3f} ms  {stage['message']}"
        )
    lines.extend([
        "",
        "GENERATED PYTHON",
        "",
        generated,
        "",
        "BEHAVIOURAL TESTING",
        "",
        f"Result: {tests['passed_tests']}/{tests['total_tests']} tests passed.",
    ])
    for case in tests["results"]:
        lines.append(
            f"- [{case['status']}] {case['name']}: input={test_inputs.get(case['name'], [])} "
            f"expected={case['expected_output']} actual={case['actual_output']}"
        )
    lines.extend([
        "",
        "ARTEFACT ORDER FOR THE VIDEO",
        "",
        "1. source_pseudocode.aj",
        "2. pseudocode_processing_report.json / processed_pseudocode.aj",
        "3. parser_report.json / ast.json / ast_visualisation.html",
        "4. flow_diagram.json / flow_diagram.html / flow_diagram.drawio",
        "5. generated_program.py / compilation_report.json",
        "6. test_cases.json / test_report.json",
        "7. pipeline_report.json",
        "",
        "NOTE",
        "Absolute run-local path fields are normalised to package-relative paths after",
        "generation so the bundled example remains portable. Timings are real but",
        "environment-dependent.",
        "",
    ])
    (EXAMPLES / "run_summary.txt").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    spec = json.loads((EXAMPLES / "test_cases.json").read_text(encoding="utf-8"))
    tests = [
        TestCase(
            name=item["name"],
            standard_input=item.get("standard_input", []),
            expected_output=item.get("expected_output"),
            category=item.get("category", "DEMONSTRATION"),
        )
        for item in spec["tests"]
    ]
    profile = PseudocodeProfile(spec["pseudocode_profile"])
    source = (EXAMPLES / "source_pseudocode.aj").read_text(encoding="utf-8")

    result = NLFlowDiagramEncoderPipeline().run(
        pseudocode=source,
        output_directory=EXAMPLES,
        test_cases=tests,
        open_visualisations=False,
        pseudocode_profile=profile,
    )
    _normalise_packaged_paths()
    _write_summary()
    print((EXAMPLES / "run_summary.txt").read_text(encoding="utf-8"))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
