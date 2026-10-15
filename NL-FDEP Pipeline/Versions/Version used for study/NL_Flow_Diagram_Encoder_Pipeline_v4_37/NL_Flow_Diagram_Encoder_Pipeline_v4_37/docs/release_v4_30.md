# NL-FDEP v4.30 release note

## Purpose

v4.30 corrects a provenance/currentness defect exposed by Algorithm 50 after its optional NumPy and Matplotlib dependencies were installed. In v4.29, source, reference, test, rubric and pipeline hashes could all remain unchanged, so a previous `BEHAVIOURAL_NOT_EVALUATED` / `MISSING_DEPENDENCY` calibration was incorrectly reusable as `SKIPPED_CURRENT` even after the required modules became available.

## Change

- `manifest.json` schema advances from 1.1 to 1.2.
- The manifest records a `dependency_environment` for modules explicitly named by Common Test `requires_modules`.
- Currentness includes a SHA-256 fingerprint of module availability and installed distribution version.
- Installing/removing/upgrading a declared dependency invalidates the affected calibration on the next run.
- Suites declaring no external modules retain normal resume behaviour.

## Unchanged study contracts

- Baseline Benchmark Folder profile: `AJ_DIALECT_STRICT`.
- AJ dialect/language version: 1.4.
- Scoring Rubric: 1.1.
- Scoring Schema: 1.4.
- Common Test Design: 1.1.
- Test-spec schema: 1.2.
- Common Test executable content: 50 suites / 113 tests.
- v4.29 Algorithm 50 NumPy/Matplotlib lowering remains unchanged.

## Regression evidence

New regression coverage proves that an unavailable-to-available dependency transition and an installed dependency version change both invalidate a prior manifest, while a suite with no declared external modules remains resumable.
