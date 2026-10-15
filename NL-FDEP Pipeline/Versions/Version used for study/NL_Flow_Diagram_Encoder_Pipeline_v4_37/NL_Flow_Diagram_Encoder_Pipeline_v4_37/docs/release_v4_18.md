# NL-FDEP v4.18 — study-safety and artefact-integrity hardening

Pipeline: **NL-FDEP v4.18**  
Dialect: **AJ_24038155 Dialect v1.4**  
Rubric: **v1.0 criteria unchanged**

## Purpose

v4.18 fixes eight study-infrastructure defects found during a read-only audit of v4.17. No AJ syntax, canonicalisation semantics, AST semantics, flow semantics, or Python lowering rules are changed.

## Fixes

1. **Stale per-algorithm artefact isolation**
   - Before a genuine reprocessing run, the previous current-view contents of `pipeline_artifacts/` are moved to `pipeline_artifacts/run_history/<previous_run_id>/`.
   - The new run starts with a clean current view, preventing old generated Python, AST, test, flow, or score files from surviving into a failed/new result.
   - Archived runs include `archive_metadata.json`.

2. **Resume completeness hardening**
   - `SKIPPED_CURRENT` now requires a current manifest, a terminal manifest status matching `pipeline_report.json`, and the complete scoring/questionnaire/flow-mediation artefact set.
   - Baseline runs additionally require reference-validation and baseline-comparison artefacts.
   - A current human review with an incomplete artefact set is protected as `REVIEW_PROTECTED_INCOMPLETE` rather than silently treated as complete.

3. **Unscored failures retained in aggregate analysis**
   - Algorithms that fail before `final_score.json` are represented in `algorithm_scores.json/.csv` with `Scored=false` and `NOT_EVALUABLE` criterion values rather than disappearing.
   - Missing expected algorithm folders detected by preflight are also represented as `PREFLIGHT_FAILURE`/`NOT_RUN` rows.
   - Whole-study summaries report `ScoredAlgorithms`, `UnscoredAlgorithms`, and per-metric evaluable denominators.

4. **Pipeline success separated from baseline calibration**
   - Batch reports retain pipeline status counts and add `calibration_status_counts` for baseline runs.
   - The PyCharm runner now prints `Pipeline status counts` and, for baseline mode, `Baseline calibration counts` separately.
   - A pipeline `SUCCESS` is therefore no longer presented as equivalent to independently validated baseline calibration.

5. **No invented behavioural defaults**
   - Unspecified expected output is no longer silently treated as `[]`.
   - Unspecified expected return code is no longer silently treated as `0`.
   - The test harness checks only expectation fields that are actually supplied or legitimately derived.

6. **Reference timeout/error fail-closed behaviour**
   - If a reference execution does not complete, omitted expectations are not manufactured.
   - A test with no remaining evaluable expectation is recorded as `NOT_EVALUABLE` and is not executed against generated Python.

7. **Validated-reference requirement for derived model-test oracles**
   - A baseline reference Python implementation may derive omitted expectations for model-result runs only when its `baseline_reference_validation.json` status is exactly `VALIDATED`.
   - Missing, `REVIEW_REQUIRED`, `NOT_EVALUATED`, or `FAILED` reference validation blocks reference-derived expectations; explicit researcher expectations remain usable.
   - Blocking reason and oracle eligibility are recorded in benchmark metadata.

8. **Stale batch-failure cleanup through run archiving**
   - A later successful retry no longer leaves an old current-view `batch_failure.json` beside successful artefacts; it is preserved only in the prior run archive.

## Batch/report schema

- Batch report schema: **1.3**.
- Existing `status_counts` remains for compatibility.
- `pipeline_status_counts` explicitly names pipeline execution status.
- `calibration_status_counts` is populated for baseline runs.
- Per-algorithm batch records include calibration/reference-validation fields where applicable.

## Validation

- `pytest`: **1,204 passed, 3 skipped, 5 subtests passed**.
- `unittest`: **354 passed, 1 skipped**.
- Three existing pytest collection warnings for the `TestCase` dataclass remain warnings only.
- Targeted regressions cover all eight defects above.
