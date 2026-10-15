# NL-FDEP v4.20 study folder layout

## Baseline calibration folder

```text
Baselines/
├── Pseudocode/
│   └── Algorithm - n/
│       ├── Algorithm n Pseudocode.txt
│       └── pipeline_artifacts/
└── Python/
    └── Algorithm - n/
        ├── Algorithm n Baseline Python code.txt
        # or Algorithm n Baseline Python code.py
        └── Algorithm n Tests.json
```

The baseline Python is the trusted behavioural reference. `Algorithm n Tests.json` is the baseline-owned common test specification used to exercise both the baseline-pseudocode pipeline result and experimental-pseudocode pipeline results.

Tests may contain explicit expected output/return/error values. When they do, those values independently validate the baseline Python. Input-only tests are also permitted: the frozen baseline Python supplies the expected observable result and is labelled `TRUSTED_REFERENCE`, not `VALIDATED`.

A baseline run produces a calibration score. Experimental runs using that baseline report their behavioural score on the same common test set and a descriptive percentage-point delta from calibration.
