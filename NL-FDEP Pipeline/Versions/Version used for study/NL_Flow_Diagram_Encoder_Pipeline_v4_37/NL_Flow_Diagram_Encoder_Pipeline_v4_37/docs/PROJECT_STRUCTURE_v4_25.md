# NL-FDEP v4.25 project structure

The grouped project layout and packaged Common Test v1.1 resource directory remain unchanged from v4.24.

## Key v4.25 changes

- `study components/study_batch.py` — separates measured calibration availability from behavioural agreement and accepts current evaluated calibration artefacts even when the legacy overall pipeline status is `FAILURE`.
- `pycharm_runner.py` — recognises current partial benchmarks, avoids repeated recalibration loops, reports evaluated/unavailable calibration counts, and permits explicit continuation with partial baseline-relative coverage.
- `docs/release_v4_25.md` — records the corrected baseline-calibration state model.

The runtime-selected Baseline benchmark still supplies `pseudocode/` and `python/`; it is not bundled into or rewritten by NL-FDEP.

Packaged Common Tests remain under `study data/common tests v1.1/` with 50 suites and 113 executable tests.
