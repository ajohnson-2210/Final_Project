# NL-FDEP v4.19 project structure

The project structure is unchanged from v4.18. The PyCharm runner remains visible at the package root; manifests, parser/compiler/pipeline/study/CLI/flow components, examples, docs and tests remain grouped in their existing folders.

## Baseline study input convention

```text
Baselines/
├── Pseudocode/
│   └── Algorithm - n/
│       └── Algorithm n Pseudocode.txt
└── Python/
    └── Algorithm - n/
        ├── Algorithm n Baseline Python code.txt   # accepted
        # or Algorithm n Baseline Python code.py   # accepted
        └── Algorithm n Tests.json                 # required for behavioural calibration
```

Legacy `Algorithm n Python.py` and the historical exactly-one-`.py` fallback remain supported. Multiple explicitly recognised reference files are treated as ambiguous rather than guessed.
