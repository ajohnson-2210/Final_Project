# NL-FDEP v4.21 study folder layout

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

`Algorithm n Tests.json` is the common test set for both baseline calibration and experimental/model comparison. v4.21 test documents may include suite-level evidence-adequacy metadata plus test-level `criteria_links`, `random_seed`, `environment`, and `requires_modules`.

The frozen baseline Python and pseudocode are not altered by the test pack. Test controls are study fixtures.
