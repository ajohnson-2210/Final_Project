# NL-FDEP v4.22 study folder layout

The baseline folder remains external to the pipeline package:

```text
Baselines/
├── Pseudocode/
│   └── Algorithm - n/
│       └── Algorithm n Pseudocode.txt
└── Python/
    └── Algorithm - n/
        ├── Algorithm n Baseline Python code.txt   # or .py
        └── Algorithm n Tests.json
```

`Algorithm n Tests.json` remains the common test set for both baseline calibration and experimental comparison. Test Design v1.1 / test-spec schema v1.2 may declare:

- suite-level `evidence_adequacy`, `evidence_summary`, `coverage_dimensions`, `coverage_basis`, `interpretation_guidance`, `coverage_limitations`, `manual_review_targets`, and `requires_pipeline_features`;
- test-level `category`, `criteria_links`, `random_seed`, `environment`, `requires_modules`, and execution timeout metadata.

The frozen baseline Python and pseudocode are not altered by the test pack. Test metadata is study evidence, not source-code repair.
