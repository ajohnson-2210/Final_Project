# NL-FDEP v4.35 RC10

## Baseline calibration / Common Tests methodology correction

RC10 corrects the calibration regression introduced in RC8 and inherited by RC9. The established baseline and transformation pipeline are unchanged. The regression was caused by promoting eight newly proposed valid-domain edge cases directly into the core calibration/scoring stream before baseline pre-freeze validation.

The active pack is now **Common Tests v1.4.1** (schema 1.6), still containing 50 suites and 156 declared cases. The historical v1.4 pack is retained unchanged.

### PRE_FREEZE_VALIDATION stream

Eight RC8 additions are retained as candidate evidence but quarantined from scoring:

- Algorithm 12: 1×1 and 2×2 diagonal-sum cases
- Algorithm 44: singleton and all-negative Kadane cases
- Algorithm 45: 1×1 and rectangular equal-size matrix-addition cases
- Algorithm 46: 1×1 and identity matrix-multiplication cases

`PRE_FREEZE_VALIDATION` cases are executed by the semantic harness when possible and reported in `semantic_test_report.json`, but they do not affect:

- baseline calibration;
- pipeline SUCCESS/FAILURE;
- experimental Common Test accuracy;
- experimental semantic behavioural score;
- automated rubric scoring; or
- Semantic Boundary Variance.

Promotion to `CORE_BEHAVIOURAL` requires explicit validation against the established baseline before the study pack is frozen.

### Preserved changes

- Algorithm 22 remains `NON_NEGATIVE_INTEGER`; `0! = 1` remains a frozen core test.
- Algorithm 33 zero remains valid core behaviour.
- Semantic Boundary Variance remains a separate descriptive stream.
- RC7 49/50 degraded baseline-readiness override remains session-only.
- RC9 automatic dashboard generation remains enabled and non-blocking.
