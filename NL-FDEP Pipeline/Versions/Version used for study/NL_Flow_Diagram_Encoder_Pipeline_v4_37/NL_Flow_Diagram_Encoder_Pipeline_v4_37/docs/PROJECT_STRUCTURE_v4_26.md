# NL-FDEP v4.26 project structure

The grouped layout remains unchanged. v4.26 changes benchmark profile control and provenance only.

## Key v4.26 controls

- `pycharm_runner.py` — fixes baseline benchmark processing to `AJ_DIALECT_STRICT`; experimental profiles remain independently selectable.
- `study components/study_batch.py` — uses Strict as the baseline calibration profile and validates baseline-relative calibration provenance against it.
- `study components/study_cli.py` — baseline CLI defaults to Strict.
- `study data/common tests v1.1/` — packaged 50-suite / 113-test common behavioural resource pack.
- `docs/common_test_design_v1_1.md` and `docs/common_test_suite_manifest_v1_1.json` — unchanged test design semantics, retargeted to v4.26 packaging.
