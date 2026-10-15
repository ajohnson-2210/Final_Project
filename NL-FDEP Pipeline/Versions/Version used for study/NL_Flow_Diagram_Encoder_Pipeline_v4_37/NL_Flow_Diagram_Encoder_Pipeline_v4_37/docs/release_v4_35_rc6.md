# NL-FDEP v4.35 Release Candidate 6

v4.35 RC6 retains the RC5 session-scoped baseline readiness gate, Common Tests v1.3 / test-spec schema v1.4, AJ_24038155 Dialect v1.5, frozen model-neutral semantic evaluation, and the successful per-process multi-dataset LLM workflow. RC6 changes the study-score finalisation semantics so automated and human rubric assessment are retained as parallel streams instead of criterion-level human substitution.

## Parallel automated and human rubric scoring

RC5 stored both automated and human criterion evidence but, when a human score was present, the `final_assessment` field substituted the human criterion score for the automated value. That behaviour did not match the intended study methodology.

RC6 removes criterion substitution. Every C1-P4 criterion now retains:

- the immutable `automated_assessment`;
- the independent `human_assessment` when supplied;
- a descriptive `score_comparison` containing agreement and numeric difference where available.

No human criterion overwrites an automated criterion.

## Equal-weight overall rubric score

RC6 adds a top-level `rubric_scores` object containing:

- `automated.percentage`;
- `human.percentage`;
- `combined.percentage`.

The combined percentage is available only after all sixteen human rubric criteria have been explicitly completed with `0`, `1`, `2`, or `NA`.

When complete:

```text
combined = (automated rubric percentage + human rubric percentage) / 2
```

The weights are fixed at 0.5 automated / 0.5 human. Partial human reviews remain available for comparison but do not generate a combined final rubric score.

## Behavioural readout remains unchanged

RC6 deliberately does **not** combine the rubric score with the Common Test behavioural metrics. The existing batch console readout remains the preferred behavioural reporting surface:

```text
Mean experimental semantic behavioural score: <value>
Aggregate task-semantic test accuracy: <value>
```

The first is the mean of per-algorithm evaluable semantic behavioural percentages. The second is the pooled pass rate over all evaluable frozen task-semantic Common Tests. They remain separate from automated, human and combined rubric percentages.

## Analysis outputs

`algorithm_scores.csv/json`, `all_models_scores.csv`, `criterion_evidence.csv`, and `human_review_status.csv` now expose explicit parallel fields, including:

- `AutomatedRubricPercent`;
- `HumanRubricPercent`;
- `CombinedRubricPercent`;
- `HumanRubricComplete`;
- human C1-P4 values/statuses alongside automated C1-P4 values/statuses;
- human and combined stage percentages where available.

The legacy C1-P4 flattened columns remain the automated stream. This prevents old criterion-level `final_assessment` substitution from silently changing the automated analysis columns.

## Returned human review on resume

If `human_review.json` is placed in a current algorithm scoring folder, a subsequent batch run refreshes `final_score.json` before returning `SKIPPED_REVIEWED`. This allows completed human review to be combined without reprocessing or modifying the current pipeline artefacts.

## Schema changes

- Scoring schema: **1.5** (from 1.4).
- Human-review questionnaire schema: **1.3** (from 1.2).
- Rubric questions and anchors remain **Scoring Rubric v1.1**.
- Pipeline version remains **4.35**.
- Common Tests remain **v1.3**, 50 suites / 113 tests.

See `docs/study_scoring_method_v1_1.md` for the authoritative combination method.

## RC6 regression coverage

RC6 adds regression coverage proving that:

- provisional automated scores expose an automated rubric percentage but no combined percentage;
- partial human review never substitutes criterion scores and never creates a combined percentage;
- a complete sixteen-criterion human review creates the exact 50:50 arithmetic mean of the two overall rubric percentages;
- behavioural-testing evidence remains byte-for-byte semantically unchanged by score combination;
- analysis exports expose automated, human and combined rubric percentages separately;
- a manually returned human review is combined on resume while the pipeline artefacts remain `SKIPPED_REVIEWED`;
- RC5 session-state lifecycle behaviour and baseline isolation remain intact.

Validation for this RC6 package:

- `pytest`: 1,293 passed, 3 skipped, 5 subtests passed;
- `unittest` with release component directories on `PYTHONPATH`: 420 passed, 1 skipped.

This build remains a release candidate and is not yet the final study freeze.
