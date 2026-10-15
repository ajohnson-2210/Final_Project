# NL-FDEP v4.07 — Study Batch, Benchmark, Scoring and Human Review Layer

## Scope

v4.07 adds the study orchestration and evidence-scoring layer around the frozen AJ_24038155 Dialect v1.2 pipeline. The release is intentionally not a compiler-completeness expansion. Its purpose is to make the existing transformation pipeline usable as a reproducible experimental instrument across model-response folders and a baseline benchmark.

## Study-folder batch processing

The new batch route accepts a folder containing immediate child directories named:

- `Algorithm - 1`
- `Algorithm - 2`
- ...

Each algorithm folder must contain a pseudocode source named exactly (case-insensitive fallback):

- `Algorithm 1 Pseudocode.txt`
- `Algorithm 2 Pseudocode.txt`
- ...

The folder number and source filename number must agree. Algorithms are processed independently and sorted numerically. A failure in one algorithm does not stop later algorithms.

Generated evidence is written inside the corresponding algorithm folder at `pipeline_artifacts/`; the original model response is never overwritten.

## Baseline benchmark

A baseline root is expected to contain:

```text
Baseline/
├── pseudocode/
│   └── Algorithm - n/
│       └── Algorithm n Pseudocode.txt
└── python/
    └── Algorithm - n/
        ├── Algorithm n Python.py
        └── Algorithm n Tests.json   # optional but required for behavioural agreement
```

Baseline pseudocode is processed through exactly the same canonicalisation -> AST -> flow -> Python pipeline as model responses. The generated Python is then compared with the supplied reference Python.

`baseline_python_comparison.json` always records descriptive source/normalised-Python-AST comparison when both programs exist. These structural comparisons are not scored as correctness because behaviourally equivalent programs may differ syntactically.

When `Algorithm n Tests.json` is supplied, missing expected outputs/return codes/error types are derived by executing the reference Python first. The same oracle is then applied to generated Python, producing behavioural agreement as the benchmark correctness measure.

## Evidence-based automated scoring

The versioned master rubric is stored at `docs/scoring_rubric_v1_0.json` and contains:

- G1 source-sufficiency gate;
- C1-C4 canonicalisation questions;
- A1-A4 AST semantic-alignment questions;
- F1-F4 flow-diagram logical-structure questions;
- P1-P4 generated-Python correctness questions;
- 0/1/2/NA anchors;
- academic-basis metadata.

Each algorithm receives:

```text
pipeline_artifacts/scoring/
├── automated_score.json
├── scoring_evidence.json
├── human_review_questionnaire.json
├── human_review_questionnaire.html
└── final_score.json
```

Every criterion record contains the full question, automated score, status, confidence, deterministic scoring-rule ID, justification and evidence references. `final_score.json` is explicitly marked provisional until a human review is supplied.

## Human verification and adjudication

The generated HTML questionnaire is self-contained and allows a reviewer to record:

- G1 source sufficiency;
- human 0/1/2/NA score for all sixteen stage criteria;
- agreement/disagreement with the automated assessment;
- semantic-issue flag;
- reviewer justification;
- first semantic-loss stage;
- final Python fidelity judgement;
- overall reviewer confidence and observations.

The form downloads `human_review.json`. If this file is placed back in the algorithm's `pipeline_artifacts/scoring/` folder, `adjudication.py` preserves both automated and human scores and updates `final_score.json` with human-adjudicated values where available.

## Analysis-ready outputs

Each batch produces `study_analysis/` containing:

- `batch_report.json`
- `batch_report.csv`
- `algorithm_scores.json`
- `algorithm_scores.csv`
- `criterion_evidence.csv`
- `review_queue.csv`
- `flowchart_impact.csv`
- `human_review_status.csv`

The flattened algorithm table includes stage percentages, C1-P4 scores, behavioural accuracy, first semantic-loss stage, failure taxonomy, flowchart delta, and simple control-flow complexity measures.

## Pipeline stage statuses

The pseudocode pipeline now distinguishes:

- `SUCCESS`
- `EXPECTED_FAILURE`
- `FAILURE`
- `NOT_RUN`

An unresolved source abstraction that the compiler deliberately refuses to invent is recorded as `EXPECTED_FAILURE`. No empty/fake generated Python artefact is created for that case, and downstream behavioural testing is marked `NOT_RUN`.

## Flow-diagram semantic correction

While validating the new flow scorer, v4.06 exposed a semantic visualisation defect: terminal/control-transfer nodes inside loops could be treated as ordinary fallthrough finals. In particular, a `BREAK` nested in an `IF` could be connected back to the loop decision rather than to the statement after the loop.

v4.07 corrects flow-graph routing so that:

- `BREAK` exits the nearest loop and then follows the post-loop continuation;
- `CONTINUE` routes directly to the nearest loop decision;
- `RETURN`, `RAISE`, and `STOP` do not fall through to later statements or loop back;
- nested-loop `BREAK` exits only the innermost loop.

The structured AST and Python compiler semantics were already correct; this change corrects the generated flow diagram's logical structure. Regression coverage is in `tests/test_flow_terminal_control_semantics_v4_07.py`.

## Validation

- pytest: 1,152 passed, 3 skipped, 5 subtests passed.
- unittest discovery (`python -m unittest discover -s tests -q`): 339 passed, 1 skipped.

No AJ_24038155 Dialect v1.2 source-language rule is changed by v4.07.
