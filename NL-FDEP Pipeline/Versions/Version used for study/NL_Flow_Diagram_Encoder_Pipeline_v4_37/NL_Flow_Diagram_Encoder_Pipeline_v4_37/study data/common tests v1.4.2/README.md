# Common Tests v1.4.2 — Frozen Task-Semantic Evaluation + Pre-Freeze Validation + Semantic Boundary Variance

Common Tests v1.4.2 contains 50 suites and 156 declared cases. It is the RC10 methodology correction to v1.4. The historical v1.4 pack is retained unchanged for provenance.

## Separate streams

- **CORE_BEHAVIOURAL** contributes to task-semantic Common Test accuracy, baseline calibration, and the existing experimental semantic behavioural score.
- **PRE_FREEZE_VALIDATION** contains candidate valid-domain coverage expansions that have not yet passed the established-baseline validation gate. These cases are executed descriptively by the semantic harness but never affect baseline calibration, experimental core accuracy, rubric scoring, or pipeline SUCCESS/FAILURE.
- **SEMANTIC_BOUNDARY_PROBE** is observational and never changes core behavioural accuracy. It reports **Semantic Boundary Variance (SBV)**: the percentage of evaluable out-of-domain probes that the generated implementation accepts and processes.

The semantic contract remains authoritative for the intended domain. The established baseline may validate candidate fixtures before promotion into CORE_BEHAVIOURAL, but baseline behaviour does not redefine the task contract and is never used as an experimental runtime oracle.

## RC10 quarantine

The eight RC8 additions that caused the RC9 baseline calibration regression are retained, not deleted, but moved to PRE_FREEZE_VALIDATION:

- Algorithm 12: 1×1 and 2×2 diagonal-sum cases
- Algorithm 44: singleton and all-negative Kadane cases
- Algorithm 45: 1×1 and rectangular equal-size matrix-addition cases
- Algorithm 46: 1×1 and identity matrix-multiplication cases

The original three v1.3 core cases for each of these algorithms remain the scoring/calibration surface until the provisional cases are explicitly validated.

## v1.4.2 correction

Algorithm 1 semantic-contract wording corrected from “True iff both strings contain the same multiset of characters.” to “True if both strings contain the same multiset of characters.” No test inputs, expected outputs, scoring streams, or case counts changed. Historical v1.4.1 remains retained unchanged for provenance.
