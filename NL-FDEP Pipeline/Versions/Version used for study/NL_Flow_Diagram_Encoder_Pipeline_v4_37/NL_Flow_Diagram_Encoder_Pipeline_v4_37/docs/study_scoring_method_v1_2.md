# Study scoring method v1.2

## Overview

The study retains three conceptually separate evidence families:

1. **Core behavioural evidence** from frozen task-semantic Common Tests.
2. **Semantic Boundary Variance (SBV)** from out-of-domain observational probes.
3. **Rubric evidence** from parallel automated and human C1-P4 review streams.

None of these streams silently replaces another.

## Core behavioural measures

The existing behavioural outputs remain unchanged in meaning:

- **Per-algorithm semantic behavioural percentage** — passed core semantic tests divided by evaluable core semantic tests for that algorithm.
- **Mean experimental semantic behavioural score** — mean of evaluable per-algorithm percentages in a dataset.
- **Aggregate task-semantic Common Test accuracy** — total passed evaluable core semantic tests divided by total evaluable core semantic tests across the dataset.

Cases tagged `SEMANTIC_BOUNDARY_PROBE` are excluded from all three calculations.

## Semantic Boundary Variance

SBV is a separate descriptive measure:

```text
SBV (%) = out-of-domain probes accepted / evaluable out-of-domain probes × 100
```

It measures semantic-domain extension, not core correctness. The pipeline also records controlled rejections, incidental failures and non-evaluable probes separately.

SBV is not averaged into the automated rubric, human rubric, combined rubric, semantic behavioural score or Common Test accuracy in RC8.

## Rubric streams

The automated and human rubric streams remain as defined in scoring method v1.1. Once all sixteen human C1-P4 criteria are explicitly completed and both overall percentages are evaluable:

```text
Combined Rubric Percentage
    = (Automated Rubric Percentage + Human Rubric Percentage) / 2
```

Automated and human rubric streams each carry 50% weight.

## Presentation-level combined behavioural measure

For analysis/presentation, the study may display the **Mean Experimental Semantic Behavioural Score** and **Aggregate Common Test Accuracy** side by side and discuss their equal-weight arithmetic mean as a **Combined Behavioural Measure**. This is an analysis-level summary and does not replace either source metric.

SBV should remain alongside that combined behavioural measure rather than being folded into it until a final weighting policy is frozen before the definitive experiment.
