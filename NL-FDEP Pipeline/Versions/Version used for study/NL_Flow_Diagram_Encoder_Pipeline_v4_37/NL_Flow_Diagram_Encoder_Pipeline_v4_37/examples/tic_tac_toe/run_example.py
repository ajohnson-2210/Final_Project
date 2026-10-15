"""Reproduce the NL-FDEP v4.37 Tic-Tac-Toe Draw.io-input example."""

from __future__ import annotations

import json
from pathlib import Path
import sys

EXAMPLE = Path(__file__).resolve().parent
ROOT = EXAMPLE.parents[1]
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
from flow_input_pipeline import DrawIOFlowInputPipeline


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
    pipeline_path = EXAMPLE / "pipeline_report.json"
    pipeline = json.loads(pipeline_path.read_text(encoding="utf-8"))
    pipeline["output_files"] = {
        key: _portable_path(value) for key, value in pipeline["output_files"].items()
    }
    if pipeline.get("test_report"):
        pipeline["test_report"]["program_path"] = _portable_path(
            pipeline["test_report"].get("program_path")
        )
    pipeline_path.write_text(json.dumps(pipeline, indent=2) + "\n", encoding="utf-8")

    compilation_path = EXAMPLE / "compilation_report.json"
    compilation = json.loads(compilation_path.read_text(encoding="utf-8"))
    compilation["source_file"] = _portable_path(compilation.get("source_file"))
    compilation_path.write_text(json.dumps(compilation, indent=2) + "\n", encoding="utf-8")

    tests_path = EXAMPLE / "test_report.json"
    tests = json.loads(tests_path.read_text(encoding="utf-8"))
    tests["program_path"] = _portable_path(tests.get("program_path"))
    tests_path.write_text(json.dumps(tests, indent=2) + "\n", encoding="utf-8")


def _write_summary() -> None:
    pipeline = json.loads((EXAMPLE / "pipeline_report.json").read_text(encoding="utf-8"))
    tests = json.loads((EXAMPLE / "test_report.json").read_text(encoding="utf-8"))
    test_spec = json.loads((EXAMPLE / "test_cases.json").read_text(encoding="utf-8"))
    test_inputs = {item["name"]: item.get("standard_input", []) for item in test_spec["tests"]}
    generated = (EXAMPLE / "generated_program.py").read_text(encoding="utf-8").strip()

    lines = [
        "NL-FDEP v4.37 — TIC-TAC-TOE DRAW.IO INPUT RUN",
        "=" * 55,
        "",
        "PURPOSE",
        "A presentation-ready, non-batch run of the Draw.io input route.",
        "The existing Tic-Tac-Toe flow diagram is imported as the input, validated,",
        "compiled to Python, represented as a Python AST, and behaviourally executed.",
        "",
        "INPUT",
        "examples/tic_tac_toe/tic_tac_toe.drawio",
        "",
        "PIPELINE STAGES",
        "",
    ]
    for stage in pipeline["stages"]:
        lines.append(
            f"[{stage['status']}] {stage['name']:<30} "
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
            f"- [{case['status']}] {case['name']}: moves={test_inputs.get(case['name'], [])}"
        )
        if case["actual_output"]:
            lines.append(f"  observed: {case['actual_output'][-1]}")
    lines.extend([
        "",
        "ARTEFACT ORDER FOR THE VIDEO",
        "",
        "1. tic_tac_toe.drawio — input flow diagram",
        "2. pipeline_report.json — import and processing stages",
        "3. generated_program.py / compilation_report.json — generated executable",
        "4. ast.json / ast_adjacency_list.json / ast_visualisation.html — generated Python AST",
        "5. test_cases.json / test_report.json — two genuine behavioural executions",
        "",
        "NOTE",
        "This is a single Draw.io-input pipeline demonstration. It is not a batch LLM run",
        "and it is not part of the frozen Common Tests used for experimental scoring.",
        "Absolute run-local paths are normalised to package-relative paths after generation.",
        "",
    ])
    (EXAMPLE / "run_summary.txt").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    spec = json.loads((EXAMPLE / "test_cases.json").read_text(encoding="utf-8"))
    tests = [
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
        input_path=EXAMPLE / "tic_tac_toe.drawio",
        output_directory=EXAMPLE,
        test_cases=tests,
        open_visualisations=False,
    )
    _normalise_packaged_paths()
    _write_summary()
    print((EXAMPLE / "run_summary.txt").read_text(encoding="utf-8"))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
