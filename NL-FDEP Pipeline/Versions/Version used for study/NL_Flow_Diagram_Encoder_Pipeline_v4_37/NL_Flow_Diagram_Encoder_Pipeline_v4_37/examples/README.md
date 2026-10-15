# Presentation-ready pipeline examples — NL-FDEP v4.37

The `examples/` directory contains two coherent **single-input** NL-FDEP runs for presentation and inspection. Neither example is an LLM batch, baseline calibration, study-results folder, or substitute for the frozen Common Tests. Every generated artefact in these demonstrations comes from a real v4.37 pipeline invocation.

## Example 1 — pseudocode input

The files directly in `examples/` form one complete `NLFlowDiagramEncoderPipeline` run.

`source_pseudocode.aj` reads a non-negative integer `Number`, converts the input explicitly to an integer, returns `0` at the zero boundary, otherwise sums the integers from `1` through `Number`, and outputs the result. The task was chosen because it produces an easy-to-explain AST and a flow diagram containing input, assignment, a decision, a loop and output.

`test_cases.json` supplies four local demonstration cases: `0 -> 0`, `1 -> 1`, `5 -> 15`, and `10 -> 55`. They are not part of the frozen study Common Tests.

### Artefact sequence

Use the files in this order when presenting the pseudocode route:

1. `source_pseudocode.aj` — source supplied to the pipeline.
2. `pseudocode_processing_report.json` and `processed_pseudocode.aj` — profile-processing evidence and canonical source passed to the parser.
3. `parser_report.json`, `ast.json`, and `ast_visualisation.html` — parsing/static-semantic evidence and the AST.
4. `flow_diagram.json`, `flow_diagram.html`, and `flow_diagram.drawio` — machine-readable and visual flow representations.
5. `generated_program.py` and `compilation_report.json` — Python generated from the flow representation.
6. `test_cases.json` and `test_report.json` — behavioural inputs, expected outputs and observed results.
7. `pipeline_report.json` — the end-to-end status record tying all stages together.
8. `run_summary.txt` — concise narration aid containing the real stage statuses and test outcome.

The bundled run finishes with every computational stage at `SUCCESS` and all four behavioural cases passing.

### Reproduce the pseudocode run

From the project root:

```bash
python examples/run_example.py
```

## Example 2 — Tic-Tac-Toe Draw.io input

`examples/tic_tac_toe/` is a separate real run using `tic_tac_toe.drawio` itself as the pipeline input. It demonstrates the second controlled input route:

**Draw.io flow diagram -> graph validation -> generated Python -> generated Python AST -> behavioural execution**

The bundled run includes two behavioural demonstrations: a Player 1 win and a nine-move draw. See `examples/tic_tac_toe/README.md` and `examples/tic_tac_toe/run_summary.txt` for the exact artefact order and results.

### Reproduce the Tic-Tac-Toe run

From the project root:

```bash
python examples/tic_tac_toe/run_example.py
```

## Packaging note

Both reproduction scripts invoke the actual v4.37 pipeline routes. The pipeline records absolute run-local paths, so each script performs a packaging-only normalisation after generation: absolute paths in the generated reports are converted to project-relative paths. No AST, flow graph, generated Python, stage result, behavioural result or score is altered. Runtime durations are genuine and vary by machine.

The frozen study resources remain under `study data/common tests v1.4.2/`. The Common Tests schema example formerly kept in this folder is retained as `docs/study_tests_template.json` so the presentation examples remain clearly separate from the study's scoring resources.

### Legacy example cleanup

The retired mixed-example artefacts from earlier releases are intentionally not packaged in `examples/`: `example.aj`, the `example_*` generated files, `ast_output.json`, `pycharm_example_output.txt`, the former root-level `tic_tac_toe.drawio`, and `examples/study_tests_template.json`. The current `parser_report.json` and `ast_visualisation.html` belong to the reproducible presentation pseudocode run and are not legacy leftovers.
