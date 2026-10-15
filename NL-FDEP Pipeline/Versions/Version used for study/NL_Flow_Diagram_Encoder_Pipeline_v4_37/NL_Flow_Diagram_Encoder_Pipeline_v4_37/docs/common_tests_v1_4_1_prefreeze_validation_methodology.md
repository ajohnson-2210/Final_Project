# Common Tests v1.4.1 — Pre-Freeze Validation Methodology

## Purpose

`PRE_FREEZE_VALIDATION` separates candidate valid-domain coverage expansions from the frozen behavioural scoring surface. A candidate may be plausible under the task contract without yet being safe to score. It must first be validated against the established baseline's invocation, observation and expected-result semantics.

## Streams

1. `CORE_BEHAVIOURAL` — frozen behavioural evidence. Contributes to baseline calibration and experimental task-semantic accuracy.
2. `PRE_FREEZE_VALIDATION` — candidate valid-domain tests. Executed descriptively when possible, but excluded from calibration, pipeline status, core behavioural accuracy and rubric scoring.
3. `SEMANTIC_BOUNDARY_PROBE` — out-of-domain observation used only for Semantic Boundary Variance.

## Promotion rule

A `PRE_FREEZE_VALIDATION` case may be promoted to `CORE_BEHAVIOURAL` only when, before the experimental study is frozen:

- the task contract supports the case as valid-domain behaviour;
- the established baseline can be invoked/observed correctly for the case;
- the expected result is confirmed;
- the observer/comparison rule does not introduce representation-specific false failures; and
- the same frozen case can then be applied model-neutrally to every experimental agent.

Baseline behaviour may validate the test mechanism but does not redefine the task contract. The baseline is never used as a runtime oracle during experimental scoring.

## RC10 provisional cases

Eight RC8 additions are retained as provisional after the RC9 baseline regression:

- Algorithm 12: 1×1 and 2×2 diagonal sum
- Algorithm 44: singleton and all-negative maximum subarray
- Algorithm 45: 1×1 and rectangular equal-size matrix addition
- Algorithm 46: 1×1 and identity matrix multiplication

The original three v1.3 cases for each remain the frozen core calibration/scoring surface.
