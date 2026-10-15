# Study folder layout — v4.07

## LLM result folders

```text
source_a/
└── results/
    ├── Algorithm - 1/
    │   ├── Algorithm 1 Pseudocode.txt
    │   └── pipeline_artifacts/                # generated
    ├── Algorithm - 2/
    │   ├── Algorithm 2 Pseudocode.txt
    │   └── pipeline_artifacts/
    └── study_analysis/                        # generated batch tables
```

The same layout may be used for source_b, source_c, source_d, source_e, source_f, or another dataset name. If the selected folder is literally named `results`, the dataset label is inferred from its parent directory.

## Baseline

```text
Baseline/
├── pseudocode/
│   ├── Algorithm - 1/
│   │   ├── Algorithm 1 Pseudocode.txt
│   │   └── pipeline_artifacts/
│   └── ...
├── python/
│   ├── Algorithm - 1/
│   │   ├── Algorithm 1 Python.py
│   │   └── Algorithm 1 Tests.json
│   └── ...
└── study_analysis/
```

If the reference Python file does not use `Algorithm n Python.py`, a single `.py` file in that reference algorithm folder is accepted. Ambiguous multiple Python files are not guessed.

## Behavioural test format

Either a top-level list or `{"tests": [...]}` is accepted. Example:

```json
{
  "algorithm_id": 1,
  "tests": [
    {
      "name": "standard case",
      "standard_input": ["listen", "silent"],
      "category": "NORMAL",
      "semantic_feature": "ANAGRAM_TRUE",
      "timeout_seconds": 3.0
    },
    {
      "name": "different lengths",
      "standard_input": ["cat", "cats"],
      "category": "BOUNDARY",
      "semantic_feature": "LENGTH_MISMATCH"
    }
  ]
}
```

For a baseline run, `expected_output`, `expected_return_code`, and `expected_error_type` may be omitted; they are derived from the supplied reference Python. They may also be supplied explicitly.

For non-baseline LLM runs, expected results should either be present in the test JSON or the batch API/CLI should be given `--baseline-root`, allowing the reference Python to provide the oracle.

Supported test categories are free text, but the scorer recognises `NORMAL`, `BOUNDARY`, and `ERROR_BEHAVIOUR`; P3 is scored only when at least one test is tagged `BOUNDARY` or `ERROR_BEHAVIOUR`.

## Per-algorithm generated evidence

```text
pipeline_artifacts/
├── manifest.json
├── pseudocode_processing_report.json
├── processed_pseudocode.aj
├── ast.json
├── parser_report.json
├── ast_visualisation.html
├── flow_diagram.json
├── flow_diagram.html
├── flow_diagram.drawio
├── generated_program.py                 # only when compilation succeeds
├── compilation_report.json
├── test_report.json                     # only when tests run
├── baseline_python_comparison.json      # baseline only
├── pipeline_report.json
└── scoring/
    ├── automated_score.json
    ├── scoring_evidence.json
    ├── human_review_questionnaire.json
    ├── human_review_questionnaire.html
    ├── human_review.json                 # supplied after reviewer completion
    └── final_score.json
```

If batch discovery itself fails (for example, the expected pseudocode filename is missing), `batch_failure.json` is retained in `pipeline_artifacts/` and later algorithms still run.
