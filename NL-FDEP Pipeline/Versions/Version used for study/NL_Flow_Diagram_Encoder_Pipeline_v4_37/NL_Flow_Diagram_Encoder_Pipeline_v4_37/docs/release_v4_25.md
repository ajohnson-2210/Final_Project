# NL-FDEP v4.25 — calibrated outcome availability and partial-benchmark handling

Pipeline: **NL-FDEP v4.25**  
Dialect: **AJ_24038155 Dialect v1.4 (unchanged)**  
Scoring rubric: **v1.1 (unchanged)**  
Scoring schema: **v1.4 (unchanged)**  
Common Test Design: **v1.1 / 50 suites / 113 tests (unchanged)**

## Purpose

v4.25 corrects a study-orchestration defect exposed by the first full v4.24 baseline run. The previous runner treated every overall pipeline `FAILURE` as an unavailable calibration, even when the run had reached behavioural testing and produced a valid calibration percentage. This contradicted the calibrated-baseline design introduced in v4.20, where a measured calibration remains valid even when the score is below 100%.

## Calibration availability

A baseline algorithm is now `CALIBRATED` whenever:

- the trusted/reference validation is accepted;
- behavioural calibration status is `EVALUATED`; and
- `calibration_score_percentage` is present.

This remains true when the legacy pipeline overall status is `FAILURE` solely because one or more behavioural tests disagreed with the trusted reference.

`PIPELINE_FAILURE` is reserved for algorithms that do not produce an evaluated behavioural calibration.

## Baseline-relative experimental comparison

Experimental processing now accepts every current evaluated baseline calibration independently. A partially calibrated 50-algorithm benchmark may therefore be used without inventing scores for unavailable algorithms.

Algorithms without an eligible baseline calibration are recorded as `NOT_EVALUABLE` for baseline-relative behavioural comparison. Other structural/scoring evidence remains available where the experimental pipeline can produce it.

## Dependency guard

The PyCharm runner distinguishes:

- current terminal baseline runs;
- current evaluated calibrations;
- structural/pipeline failures without calibration;
- successful runs whose behavioural tests are not evaluable.

A current partial benchmark is no longer recalibrated repeatedly merely because fewer than 50 algorithms have behavioural calibration scores. The runner presents the limitation and asks whether to continue.

## Reporting

Baseline batch reports now include:

- `evaluated_baseline_calibration_count`;
- `baseline_calibration_unavailable_count`.

Console output explicitly notes that the legacy pipeline `FAILURE` count may include measured behavioural disagreement and must not be used as the calibration-availability count.

## Compatibility

No changes are made to AJ v1.4, C1-C4/A1-A4/F1-F4/P1-P4, G2 scoring status, Common Test Design v1.1, test-spec schema v1.2, or the 113 executable tests.
