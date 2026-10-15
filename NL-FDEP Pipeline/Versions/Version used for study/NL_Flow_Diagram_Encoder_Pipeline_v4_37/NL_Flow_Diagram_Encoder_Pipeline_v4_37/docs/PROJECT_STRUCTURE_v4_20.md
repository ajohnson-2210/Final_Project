# NL-FDEP v4.20 project structure

The package structure is unchanged from v4.19. `pycharm_runner.py` remains visible at the package root and implementation files remain grouped by responsibility.

## Baseline calibration input convention

```text
Baselines/
├── Pseudocode/
│   └── Algorithm - n/
│       └── Algorithm n Pseudocode.txt
└── Python/
    └── Algorithm - n/
        ├── Algorithm n Baseline Python code.txt   # accepted
        # or Algorithm n Baseline Python code.py   # accepted
        └── Algorithm n Tests.json                 # common behavioural test set
```

Legacy `Algorithm n Python.py` and the historical exactly-one-`.py` fallback remain supported.

## Baseline output

Each baseline algorithm writes, among the existing artefacts:

```text
pipeline_artifacts/
├── baseline_reference_validation.json
├── baseline_python_comparison.json
├── baseline_calibration.json
├── generated_program.py
├── test_report.json                # when behavioural tests are evaluable
└── scoring/
```

`baseline_calibration.json` contains the behavioural pipeline calibration score against the trusted baseline Python.

## Experimental output

When an experimental results folder is processed with a baseline root, each algorithm also writes:

```text
pipeline_artifacts/
└── baseline_relative_comparison.json
```

This records the baseline calibration score, experimental behavioural score, descriptive percentage-point delta, comparison category and common-test-set status.

Batch-level `study_analysis/` retains latest-view reports plus immutable run history and now also includes `baseline_comparison.csv`.
