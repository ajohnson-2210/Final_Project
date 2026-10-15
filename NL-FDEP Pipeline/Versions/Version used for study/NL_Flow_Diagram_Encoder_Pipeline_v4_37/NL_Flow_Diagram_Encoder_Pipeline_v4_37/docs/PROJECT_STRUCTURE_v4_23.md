# NL-FDEP v4.23 project structure

The grouped project layout remains unchanged except for the pipeline-owned common-test resource directory.

## Key v4.23 additions

- `study data/common tests v1.1/` — canonical packaged location for the 50 Common Test Design v1.1 JSON suites (113 tests).
- `study components/common_test_resources.py` — resolves and validates packaged common tests and supports the merge-pack folder layout without modifying a selected baseline.
- `study components/study_batch.py` — prefers packaged Common Tests v1.1 for baseline and experimental runs, with baseline-local tests retained only as a compatibility fallback.
- `study components/study_provenance.py` — reports whether each test suite came from the packaged resource overlay or a baseline-local fallback.
- `pycharm_runner.py` — provides the v4.23 baseline dependency guard and automatic calibration offer for baseline-dependent experimental processing.

The runtime-selected Baseline benchmark still supplies `pseudocode/` and `python/`; it is not bundled into or rewritten by NL-FDEP.
