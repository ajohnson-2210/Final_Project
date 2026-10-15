# NL-FDEP v4.20 — calibrated baseline comparison design

Pipeline: **NL-FDEP v4.20**  
Dialect: **AJ_24038155 Dialect v1.4 (unchanged)**  
Rubric: **v1.0 (criteria unchanged)**  
Scoring schema: **v1.2**  
Batch schema: **v1.4**

v4.20 formalises the study design in which the frozen baseline is a **pipeline calibration benchmark** and experimental pseudocode results are compared with that calibration on the same behavioural reference and test set.

## Calibration design

For Algorithm `n`:

```text
Frozen baseline pseudocode
        -> same NL-FDEP pipeline
        -> generated baseline Python
        -> behavioural comparison with trusted baseline Python
        -> Baseline Calibration Score
```

Experimental/source pseudocode is then processed through the same pipeline:

```text
Experimental pseudocode
        -> same NL-FDEP pipeline
        -> generated experimental Python
        -> same trusted baseline Python + same baseline-owned test set
        -> Experimental Behavioural Score
```

The study reports both scores side by side plus:

`Experimental Behavioural Score - Baseline Calibration Score`

as a **descriptive percentage-point delta**. The delta is not an adjusted accuracy score and must not be interpreted as a causal estimate of model quality independent of the pipeline.

## Trusted reference semantics

A frozen baseline Python implementation with no independently supplied expected outputs is now recorded as `TRUSTED_REFERENCE`. This explicitly means that the study design accepts it as the behavioural reference; it does **not** falsely claim independent validation.

If test cases contain researcher-specified expected output/return/error values, those expectations still independently validate the baseline reference and the status remains `VALIDATED` or `FAILED` as appropriate.

Experimental runs may use baseline-derived expected outcomes only when a **current v4.20 baseline calibration artefact** exists. A bare reference file is insufficient. Recalibrating the baseline changes the calibration run ID and invalidates any cached experimental comparison against the earlier calibration.

## Calibration status

`CALIBRATED` means that a behavioural calibration score was measured. It does not mean the score is necessarily 100%. For example, a 75% baseline result remains a valid calibration measurement and can be compared descriptively with an experimental result.

## New artefacts and analysis fields

Baseline algorithm artefacts now include:

- `baseline_calibration.json`
- retained compatibility file `baseline_python_comparison.json`

Experimental algorithm artefacts include:

- `baseline_relative_comparison.json`

Analysis output now includes `baseline_comparison.csv` and the columns:

- `BaselineCalibrationPercent`
- `ExperimentalBehaviouralPercent`
- `DeltaFromBaselinePercentagePoints`
- `ComparisonToBaseline`
- `ComparisonStatus`
- `CommonTestSet`

Batch reports also include mean baseline calibration, mean experimental behavioural score, mean percentage-point delta, and comparison-to-baseline counts where evaluable.

## Common tests

`Algorithm n Tests.json` remains the baseline-owned common behavioural test specification. It may contain explicit expected outcomes or input-only cases. For input-only cases, the trusted baseline Python supplies the expected observable behaviour. Reference timeouts remain non-evaluable and do not create invented expectations.

No AJ grammar, canonicalisation, AST, flow-diagram or Python-lowering semantics are changed in v4.20.

## Regression validation

- `pytest`: **1,215 passed, 3 skipped, 5 subtests passed**
- `unittest`: **365 tests run, 1 skipped, OK**
- AJ_24038155 Dialect remains **v1.4**
- No named corpus AI-agent/vendor references detected in the distributed source tree
