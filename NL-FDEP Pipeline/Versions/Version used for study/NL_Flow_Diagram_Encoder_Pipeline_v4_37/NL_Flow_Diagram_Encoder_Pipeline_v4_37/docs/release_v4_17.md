# NL-FDEP v4.17 — analysis provenance and version-consistency fix

Pipeline: **NL-FDEP v4.17**  
Dialect: **AJ_24038155 Dialect v1.4**

## Purpose

v4.17 fixes two study-infrastructure issues without changing AJ syntax, parser semantics, AST semantics, flow semantics or Python lowering.

## Changes

1. **Correct internal pipeline version metadata**
   - `PIPELINE_VERSION` is now `4.17`.
   - Batch reports, per-algorithm manifests and scoring outputs therefore identify the actual running release.
   - Resume checks no longer treat artefacts from an older release as current merely because a stale internal version constant was left behind.

2. **Preserve batch analysis history**
   - `study_analysis/` continues to hold the latest reports at the established filenames.
   - Every batch invocation receives a unique `batch_run_id`.
   - A snapshot of the batch-level analysis is written to `study_analysis/run_history/<batch_run_id>/`.
   - Each snapshot contains `run_metadata.json`.
   - `study_analysis/latest_run.json` points to the latest snapshot.

3. **Batch schema**
   - Batch report schema is now `1.2`.
   - `batch_run_id` is included in `batch_report.json`.

## Compatibility

Existing study folder layouts remain valid. The latest top-level analysis filenames are unchanged, so existing scripts that consume `study_analysis/batch_report.json`, `algorithm_scores.csv`, and related files continue to work.
