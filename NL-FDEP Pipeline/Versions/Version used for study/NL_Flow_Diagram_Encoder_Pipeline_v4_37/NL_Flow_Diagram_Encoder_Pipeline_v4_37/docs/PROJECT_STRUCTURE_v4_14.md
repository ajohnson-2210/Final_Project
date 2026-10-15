# NL-FDEP v4.14 project structure

AJ dialect: **AJ_24038155 Dialect v1.4**

v4.14 reorganises the package without changing parser, compiler, flow, scoring or dialect semantics.

## Root

- `pycharm_runner.py` — primary interactive PyCharm entry point.
- `README.md` — release and usage documentation.
- `requirements.txt` — installable Python test dependency list; runtime pipeline code uses the standard library.
- `VERSION` — pipeline version.
- `pytest.ini` — pytest configuration.

## Grouped folders

- `manifests/` — historical and current package manifest text files.
- `flow diagram components/` — flow encoding, visualisation, draw.io import/export and flow mediation modules.
- `parser components/` — AJ parser, AST representation and pseudocode profile processing.
- `compiler components/` — AJ-to-Python compiler and behavioural test harness.
- `pipeline components/` — main pipeline orchestration and controlled input selection/resolution.
- `study components/` — batch processing, baseline benchmark, scoring, adjudication, review, provenance and study analysis.
- `cli components/` — non-GUI command-line parser entry point.
- `examples/` — all example inputs and generated/sample artefacts formerly present at project root.
- `docs/` — dialect, release, audit and research documentation.
- `tests/` — regression tests and test corpora.

## Compatibility

The project retains the existing flat Python module names internally. `pycharm_runner.py`, `tests/conftest.py`, `tests/__init__.py`, and direct CLI entry points add the component directories to `sys.path`, allowing the existing imports to work after the physical file reorganisation.
