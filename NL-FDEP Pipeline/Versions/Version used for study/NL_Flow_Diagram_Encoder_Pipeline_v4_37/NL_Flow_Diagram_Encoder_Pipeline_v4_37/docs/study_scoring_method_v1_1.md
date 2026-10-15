# Study scoring method v1.1

## Purpose

The study retains automated and human rubric assessment as two parallel evidence streams. Neither stream overwrites the other. The final combined rubric score is available only after the human reviewer has completed all sixteen C1-P4 rubric criteria using the same 0/1/2/NA scale.

This scoring method is separate from the task-semantic behavioural metrics reported by the experimental Common Tests.

## Rubric streams

For each algorithm, the automated scorer produces an **Automated Rubric Percentage** from the applicable C1-P4 criterion scores. Criteria marked `NA` / `NOT_EVALUABLE` are excluded from that stream's denominator.

The human reviewer independently completes the same sixteen criteria. A human criterion is considered completed when the reviewer explicitly records `0`, `1`, `2`, or `NA`. The **Human Rubric Percentage** is calculated from the human-review criteria with numeric scores; explicit `NA` criteria are excluded from the human denominator.

Partial human reviews are retained for agreement/disagreement analysis but do **not** create a final combined rubric percentage.

## Equal-weight combined rubric score

When all sixteen human criteria have been explicitly completed and both stream percentages are evaluable:

```text
Combined Rubric Percentage
    = (Automated Rubric Percentage + Human Rubric Percentage) / 2
```

The two rubric streams therefore have equal weight:

```text
Automated rubric = 50%
Human rubric     = 50%
```

Example:

```text
Automated Rubric Percentage = 82%
Human Rubric Percentage     = 76%
Combined Rubric Percentage  = (82 + 76) / 2 = 79%
```

The combination is performed at **overall-rubric percentage level**. Human criterion scores do not substitute for automated criterion scores, and criterion-level arithmetic means are not used as the final method.

## Behavioural metrics remain separate

The following experimental readouts are not part of the rubric-average formula:

- **Mean experimental semantic behavioural score**: the mean of the per-algorithm frozen task-semantic behavioural percentages that are evaluable.
- **Aggregate task-semantic test accuracy**: total passed evaluable task-semantic Common Tests divided by total evaluable task-semantic Common Tests.

For example, a study batch may legitimately report:

```text
Mean experimental semantic behavioural score: 84.00
Aggregate task-semantic test accuracy: 84.13
```

Those are behavioural test metrics. They remain alongside, rather than being averaged with, the automated/human rubric scores.

## Side-by-side evidence retained

`final_score.json` preserves:

- every original `automated_assessment`;
- every completed `human_assessment`;
- criterion-level agreement and human-minus-automated differences where numeric comparison is possible;
- automated stage summaries;
- human stage summaries;
- descriptive combined stage percentages after a complete human stage review;
- overall automated, human and combined rubric percentages;
- automated-human agreement percentage.

The top-level `rubric_scores` object is the authoritative source for the three overall rubric percentages.

## Completion states

- `PROVISIONAL_AUTOMATED`: no human rubric criteria have been completed.
- `HUMAN_REVIEW_PARTIAL`: at least one but fewer than all sixteen human criteria have been completed; no combined rubric percentage is available.
- `AUTOMATED_HUMAN_COMBINED`: all sixteen human criteria have been explicitly completed and the equal-weight combined rubric percentage is available.

A returned `human_review.json` is combined on the next review/adjudication action. When the study batch is rerun with current immutable artefacts, RC6 refreshes `final_score.json` before applying `SKIPPED_REVIEWED`, so a completed review can be incorporated without regenerating pipeline outputs.

## Gates and descriptive evidence

G1 Source Sufficiency and G2 Behavioural Evidence Adequacy remain non-scored gates/descriptive evidence. Automated and human gate judgements are retained side by side; the human result does not replace the automated result and neither gate is included in the combined rubric percentage.

## Reproducibility rule

The automated rubric, human rubric and combined rubric must be reported separately in analysis outputs. The study should not report a combined rubric result unless the human rubric is complete. Behavioural Common Test metrics must remain separately labelled so that rubric judgement and executable behavioural evidence are not conflated.
