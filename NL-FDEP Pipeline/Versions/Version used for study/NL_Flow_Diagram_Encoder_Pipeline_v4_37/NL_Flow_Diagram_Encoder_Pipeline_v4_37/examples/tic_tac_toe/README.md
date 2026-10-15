# Tic-Tac-Toe Draw.io-input example — NL-FDEP v4.37

This subfolder is a genuine **single-input pipeline run** using `tic_tac_toe.drawio` as the input to NL-FDEP's Draw.io route. It is intentionally separate from the pseudocode example in the parent `examples/` folder and is not an LLM batch run.

## What the run demonstrates

The route imports the existing flow diagram, validates the imported graph, compiles the flow representation to executable Python, generates an AST of the generated Python, and runs two behavioural demonstrations.

The two local demonstration cases are:

1. moves `0, 3, 1, 4, 2`, which end with **Player 1 declared the winner**;
2. moves `0, 1, 2, 4, 3, 5, 7, 6, 8`, which end with **the game declared a draw**.

These are presentation examples only and are not part of the frozen Common Tests used by the study.

## Artefact order

For a video demonstration, use the files in this order:

1. `tic_tac_toe.drawio` — the input supplied to the pipeline.
2. `pipeline_report.json` — records the Draw.io import, graph validation, Python AST generation, compilation and behavioural-testing stages.
3. `generated_program.py` and `compilation_report.json` — executable Python generated from the imported flow graph.
4. `ast.json`, `ast_adjacency_list.json` and `ast_visualisation.html` — AST evidence derived from the generated Python.
5. `test_cases.json` and `test_report.json` — behavioural inputs, expected outputs and observed results.
6. `run_summary.txt` — concise narration aid generated from the real run.

## Reproducing the run

From the project root:

```bash
python examples/tic_tac_toe/run_example.py
```

The script invokes the actual v4.37 `DrawIOFlowInputPipeline`; it does not fabricate stage results. The pipeline records absolute run-local file paths, so the script performs a packaging-only normalisation to project-relative paths after generation. Runtime timings remain genuine and can vary by machine.
