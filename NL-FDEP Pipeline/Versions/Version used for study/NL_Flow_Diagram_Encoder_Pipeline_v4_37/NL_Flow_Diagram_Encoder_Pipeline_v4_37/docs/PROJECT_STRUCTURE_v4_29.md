# NL-FDEP v4.29 project structure

The grouped layout remains unchanged. v4.29 adds compiler support for explicit NumPy/Matplotlib adapter calls used by Algorithm 50; baseline selection remains runtime-external and fixed to AJ_DIALECT_STRICT.

Key additions:
- `docs/release_v4_29.md` — external-module lowering rationale.
- `tests/test_external_numeric_visual_support_v4_29.py` — adapter compilation/headless regressions.
- `docs/optional_reference_requirements_v4_29.txt` — optional dependency note.

# NL-FDEP v4.28 project structure

The grouped project layout remains unchanged. v4.28 changes only benchmark-reference execution recognition and two Python compiler representation boundaries.

## Key v4.28 controls

- `pycharm_runner.py` — runtime input routing; baseline benchmark profile remains `AJ_DIALECT_STRICT`.
- `study components/baseline_benchmark.py` — trusted-reference validation, controlled non-mutating execution view, oracle derivation and baseline comparison.
- `compiler components/aj_python_compiler.py` — AJ-to-Python lowering including `RAISE SystemExit` and protected method alias publication.
- `study components/common_test_resources.py` — pipeline-owned Common Tests v1.1 resolution and 50-suite/113-test validation.
- `study data/common tests v1.1/` — canonical Common Test resource layer; executable test arrays unchanged.
- `docs/release_v4_28.md` — v4.28 change rationale and preserved residuals.
- `tests/test_reference_execution_contract_v4_27.py` — reference-execution and SystemExit regressions, extended for v4.28.
- `tests/test_reserved_identifier_source_baseline_v4_11.py` — protected reserved-method representation regression.

No frozen Baselines corpus is bundled into the pipeline. The baseline remains a runtime-selected external study input.
