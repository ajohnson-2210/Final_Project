# NL-FDEP v4.24 — controlled baseline profile and calibration health guard

Pipeline: **NL-FDEP v4.24**  
Dialect: **AJ_24038155 Dialect v1.4 (unchanged)**  
Scoring rubric: **v1.1 (unchanged)**  
Scoring schema: **v1.4 (unchanged)**  
Common Test Design: **v1.1 / 50 suites / 113 tests (unchanged)**

## Purpose

v4.24 corrects baseline-run orchestration discovered during the first v4.23 calibration attempt. Baseline benchmark processing now uses the controlled `GENERIC_COMPATIBILITY` pseudocode profile automatically rather than asking the user to select a profile. Experimental pseudocode processing remains user-selectable.

## Baseline profile isolation

The Baseline benchmark folder route no longer presents the pseudocode-profile chooser. Baseline calibration always uses `GENERIC_COMPATIBILITY`, matching the existing `study_cli.py` and `StudyBatchProcessor.process_baseline()` default. If an LLM-results operation triggers automatic baseline calibration, the baseline also uses this controlled profile independently of the profile selected for experimental pseudocode.

## Provenance and resume safety

The pseudocode profile is now part of manifest-currentness checks. A calibration produced with another profile cannot be resumed or mistaken for a current calibration. Baseline-dependency checks additionally require the current pipeline version, the controlled baseline profile, an eligible baseline processing status, and an evaluated calibration.

## Failure reporting

An evaluated behavioural comparison no longer hides a pipeline failure behind the headline `CALIBRATED`. Such records are labelled `CALIBRATED_WITH_<PIPELINE_STATUS>`. Unexpected baseline `FAILURE` statuses are not eligible for dependent experimental comparison. If automatic calibration produces unexpected failures, the requested experimental operation is stopped and the user is directed to the batch report.

## Compatibility

No changes are made to AJ v1.4, C1-C4/A1-A4/F1-F4/P1-P4, G2 scoring status, Common Test Design v1.1, test-spec schema v1.2, or the 113 executable tests.
