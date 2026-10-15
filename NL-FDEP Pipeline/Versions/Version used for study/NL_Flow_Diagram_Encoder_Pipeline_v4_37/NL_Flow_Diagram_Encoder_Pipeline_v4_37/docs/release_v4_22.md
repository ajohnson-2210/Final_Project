# NL-FDEP v4.22 — descriptive G2 behavioural evidence profiles

Pipeline: **NL-FDEP v4.22**  
Dialect: **AJ_24038155 Dialect v1.4 (unchanged)**  
Scoring rubric: **v1.1 (16 scored criteria unchanged)**  
Scoring schema: **v1.4**

## Purpose

v4.22 expands the existing non-scored **G2 Behavioural Evidence Adequacy** gate from a headline label into a descriptive evidence profile. The change addresses the study requirement that a one-word label such as `ADEQUATE`, `PARTIAL`, or `LIMITED` is not sufficient evidence on its own.

## G2 descriptive evidence profile

The G2 headline classification is retained for sorting and aggregation, but every scored algorithm now also records:

- `summary` — concise narrative of the available behavioural evidence;
- `test_counts` — declared, evaluable, passed, failed, and non-evaluable tests;
- `coverage_dimensions` — normal-path, branch, boundary, error, termination, and state-mutation coverage;
- `strengths` — positive evidence and reproducibility controls;
- `limitations` — explicit declared and execution-derived limits;
- `coverage_basis` — what evidence the assessment is based on;
- `interpretation` — how broadly the behavioural accuracy may legitimately be interpreted;
- `manual_review_targets` and reproducibility counts.

Coverage dimensions use `COVERED`, `PARTIALLY_COVERED`, `NOT_COVERED`, `NOT_APPLICABLE`, or `NOT_EVALUABLE`.

G2 remains **non-scored**. It never increases or decreases C1-P4 scores or the behavioural accuracy percentage.

## Common Test Design v1.1

The separately distributed 50-algorithm common test pack is updated from Test Design v1.0 to **v1.1**. The 113 behavioural tests are unchanged; each suite now additionally declares an evidence summary, six-dimensional coverage profile, coverage basis, and interpretation guidance. At runtime v4.22 combines those declarations with the actual executed/evaluable/pass counts.

The suite test-spec schema advances to **1.2** only to carry the richer metadata. Test semantics are unchanged.

## Human review and adjudication

The HTML questionnaire now shows the complete G2 profile and allows the reviewer to record an independent G2 assessment, agreement, and evidence comment. Adjudication preserves that human assessment as the final G2 result when supplied while leaving G2 outside the numerical correctness score.

## Analysis outputs

`algorithm_scores.json` and `.csv` now include the headline G2 value plus descriptive fields including G2 summary, test counts, all six coverage dimensions, strengths, limitations, coverage basis, and interpretation.

## Frozen-source policy

No frozen baseline Python or baseline pseudocode is modified by v4.22. AJ Dialect v1.4 is unchanged. The 16 scored C/A/F/P criteria remain exactly the same as rubric v1.1 in v4.21.

## Validation

- pytest: **1,220 passed, 3 skipped, 5 subtests passed**;
- unittest discovery: **370 passed, 1 skipped**;
- all 50 Test Design v1.1 JSON files loaded successfully;
- **113 tests** retained exactly from Test Design v1.0 (test arrays unchanged); only descriptive G2 metadata was added;
- PyCharm runner import smoke passed;
- no named AI-agent/vendor references detected in the distributed package;
- package caches/compiled bytecode removed before release.
