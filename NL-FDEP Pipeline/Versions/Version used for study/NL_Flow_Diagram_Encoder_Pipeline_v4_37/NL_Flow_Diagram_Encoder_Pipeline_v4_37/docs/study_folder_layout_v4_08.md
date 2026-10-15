# Study folder layout — v4.08

## LLM dataset

```text
source_a/
└── results/
    ├── Algorithm - 1/
    │   ├── Algorithm 1 Pseudocode.txt
    │   └── pipeline_artifacts/
    │       ├── manifest.json
    │       ├── processed_pseudocode.aj
    │       ├── pseudocode_processing_report.json
    │       ├── ast.json
    │       ├── parser_report.json
    │       ├── flow_diagram.json
    │       ├── flow_diagram.html
    │       ├── flow_diagram.drawio
    │       ├── generated_program.py
    │       ├── compilation_report.json
    │       ├── test_report.json                  # when tests exist
    │       ├── direct_ast_program.py             # flow mediation control, when compilable
    │       ├── direct_ast_compilation_report.json
    │       ├── direct_ast_test_report.json       # when tests exist
    │       ├── flow_mediation_analysis.json
    │       ├── pipeline_report.json
    │       └── scoring/
    │           ├── automated_score.json
    │           ├── scoring_evidence.json
    │           ├── human_review_questionnaire.json
    │           ├── human_review_questionnaire.html
    │           ├── human_review.json             # after review
    │           └── final_score.json
    └── study_analysis/
        ├── study_preflight.json
        ├── study_preflight.csv
        ├── batch_report.json
        ├── batch_report.csv
        ├── algorithm_scores.csv
        ├── criterion_evidence.csv
        ├── review_queue.csv
        ├── flowchart_impact.csv
        └── human_review_status.csv
```

## Baseline

```text
Baseline/
├── pseudocode/
│   └── Algorithm - 1/
│       ├── Algorithm 1 Pseudocode.txt
│       └── pipeline_artifacts/
│           ├── baseline_reference_validation.json
│           ├── baseline_python_comparison.json
│           └── ...same pipeline/scoring artefacts...
├── python/
│   └── Algorithm - 1/
│       ├── Algorithm 1 Python.py
│       └── Algorithm 1 Tests.json
└── study_analysis/
    ├── study_preflight.json
    └── ...analysis outputs...
```

`Algorithm n Tests.json` may contain explicit expected outputs/errors/return codes. Explicit expectations are treated as researcher-specified evidence for validating the baseline reference. Omitted expectations may be derived from the reference Python for downstream generated-vs-reference testing, but are not used to validate the reference itself.
