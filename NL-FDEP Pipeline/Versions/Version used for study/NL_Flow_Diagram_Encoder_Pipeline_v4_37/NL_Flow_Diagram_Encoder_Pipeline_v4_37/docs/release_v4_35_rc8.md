# NL-FDEP v4.35 RC8

RC8 advances the active Common Test resource to **v1.4 / test-spec schema v1.5** and introduces a separate semantic-boundary observation stream while retaining the RC7 baseline-readiness behaviour and RC6 parallel rubric semantics.

## Common Tests v1.4

- 50 suites.
- 156 declared cases.
- 107 automatically enabled **core semantic** cases.
- 30 core interaction/reference-only or human-supported cases.
- 19 declared **semantic-boundary probes**.
- 17 automatically runnable boundary probes; 2 deliberately `NOT_EVALUABLE` pending safe generic adapters.

Core behavioural cases and semantic-boundary probes are kept in separate score streams.

## Semantic Boundary Variance

Boundary probes are tagged `SEMANTIC_BOUNDARY_PROBE` and use `BOUNDARY_OBSERVATION`. They have no frozen expected semantic value and cannot affect core Common Test accuracy.

An evaluable boundary probe is classified as `OUT_OF_DOMAIN_ACCEPTED`, `CONTROLLED_REJECTION`, or `INCIDENTAL_FAILURE`. SBV is the percentage of evaluable probes classified `OUT_OF_DOMAIN_ACCEPTED`.

## Contract/test corrections

- Algorithm 22 factorial is now `NON_NEGATIVE_INTEGER`; `0! = 1` is a frozen core boundary case.
- Algorithm 33 square root now treats zero as a valid core input.
- Algorithm 20 zero/negative divisor inputs move to the semantic-boundary stream.
- Algorithm 40 metadata now reflects the actual empty-queue dequeue in its frozen sequence.
- Stale “not externally injectable” wording is removed from v1.4.
- Selected boundary-capable algorithms receive additional valid in-domain fixtures so core scoring covers more than a single representative input.

## Baseline isolation

The normal RC7 baseline gate remains unchanged: 50/50 is the full readiness state, with the explicit session-only 49/50 unavailable-calibration override retained. Boundary observations do not alter baseline calibration percentages. A baseline-generated program may be evaluated against the v1.4 semantic pack for validation/context, but experimental expected values remain static and baseline-independent.

## Analysis exports

Per-algorithm analysis adds:

- `SemanticBoundaryProbesDeclared`
- `SemanticBoundaryProbesEvaluable`
- `SemanticBoundaryAccepted`
- `SemanticBoundaryControlledRejection`
- `SemanticBoundaryIncidentalFailure`
- `SemanticBoundaryNotEvaluable`
- `SemanticBoundaryVariancePercent`

Batch reports add aggregate boundary-probe counts and aggregate/mean-algorithm SBV values for LLM datasets.

## Validation

- targeted v1.4/SBV regressions: PASS
- full pytest: 1304 passed, 3 skipped, 5 subtests passed
- full unittest: 431 passed, 1 skipped

## Final study freeze requirement

RC8 has not been run against the user's external calibrated baseline corpus in this package-validation environment. Before the definitive experimental study, run the actual baseline through Common Tests v1.4 and inspect the new semantic-boundary observations. This pre-study validation must not be used to create runtime experimental expected values or to redefine the original task contracts.
