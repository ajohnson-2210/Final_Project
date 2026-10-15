# NL-FDEP v4.23 — packaged common-test overlay and baseline dependency guard

Pipeline: **NL-FDEP v4.23**  
Dialect: **AJ_24038155 Dialect v1.4 (unchanged)**  
Scoring rubric: **v1.1 (unchanged)**  
Scoring schema: **v1.4 (unchanged)**  
Common Test Design: **v1.1 (unchanged)**  
Test-spec schema: **v1.2 (unchanged)**

## Purpose

v4.23 removes the need for users to physically merge Common Tests v1.1 into each Baseline benchmark folder. Common behavioural tests are now resolved as pipeline-owned packaged resources and virtually associated with whichever compatible baseline is selected at runtime.

## Runtime baseline remains external

The Baseline benchmark folder is still selected by the user at runtime. v4.23 does not bundle or rewrite baseline pseudocode or trusted baseline Python. The selected baseline therefore remains replaceable between runs.

## Common-test resource overlay

The canonical resource location is:

`study data/common tests v1.1/`

For every algorithm, v4.23 first resolves the packaged `Algorithm n Tests.json`. The resource resolver accepts either a flat 50-file layout or the original merge-pack style `python/Algorithm - n/Algorithm n Tests.json` layout. Baseline-local test specifications remain a backward-compatible fallback only when the packaged file for that algorithm is unavailable.

The v4.23 distribution contains the complete 50-suite / 113-test resource set. Resource validation checks file identity, JSON structure, algorithm identifiers, test-spec schema v1.2 and aggregate suite/test counts. The executable test arrays are carried forward from the supplied Test Design v1.0 pack and verified semantically unchanged; Test Design v1.1 adds the supplied descriptive G2 metadata only.

## Runner baseline dependency guard

The `LLM results folder` route requires a baseline benchmark. When the route is selected and no benchmark has yet been supplied for that run, the runner asks whether the user wants to provide one first. If the answer is no or the chooser is cancelled, the requested operation exits safely without starting a partial experimental run.

A supplied benchmark is preflight-validated. If fewer than 50 current v4.23 evaluated baseline calibrations are present, the runner asks whether calibration should be run first. When accepted, baseline calibration is performed and the original experimental operation then resumes automatically. Algorithms that still lack an eligible evaluated calibration are preserved as not evaluable rather than receiving an invented oracle.

## Scoring stability

No C1-C4, A1-A4, F1-F4 or P1-P4 scoring criterion changes in v4.23. G2 remains descriptive and non-scored. This release changes packaging, test-resource resolution, preflight provenance and runner orchestration only.

## Packaged common-test provenance

The 113 executable tests are taken from the supplied Common Tests v1.0 and Baselines Merge archives. Test Design v1.1 states that those executable tests are unchanged; v4.23 therefore enriches each suite with the supplied v1.1 descriptive G2 metadata while preserving every `tests` array. `docs/common_test_resource_build_v4_23.json` records source SHA-256 values and per-algorithm canonical test-array hashes.

## Validation

- packaged Common Tests: **50/50 suites, 113/113 tests**;
- all packaged test-spec files: **Test Design v1.1 / schema v1.2**;
- all 50 executable `tests` arrays verified semantically unchanged from the supplied v1.0 suites;
- pytest: **1,226 passed, 3 skipped, 5 subtests passed**;
- unittest discovery: **376 passed, 1 skipped**;
- v4.23 common-test overlay and baseline-dependency guard regression tests passed.
