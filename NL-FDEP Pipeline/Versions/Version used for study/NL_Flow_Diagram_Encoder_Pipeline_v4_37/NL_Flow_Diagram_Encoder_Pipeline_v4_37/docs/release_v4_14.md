# NL-FDEP v4.14 — project structure and dependency packaging

Pipeline: **NL-FDEP v4.14**  
Dialect: **AJ_24038155 Dialect v1.4**

## Change

v4.14 is a packaging and maintainability release. It does not alter AJ v1.4 syntax or semantics and does not change algorithm transformation behaviour.

The project root is intentionally reduced to the PyCharm runner and project-level files. Implementation modules are grouped into parser, compiler, flow-diagram, pipeline, study and CLI component folders. Historical manifest text files are consolidated under `manifests/`, and loose example/generated artefacts are consolidated under `examples/`.

A root `requirements.txt` is added. Runtime pipeline code uses the Python standard library; `pytest` is listed for the bundled regression suite. Tkinter remains a standard-library GUI dependency and may require the platform Python/Tk package on systems where it is not bundled.

Compatibility bootstraps preserve the existing flat module import names used by the PyCharm runner and regression tests.

## Validation

- `python -m pytest -q`: **1,198 passed, 3 skipped, 5 subtests passed**.
- `python -m unittest discover -s tests -t . -q`: **344 passed, 1 skipped**.
- PyCharm runner imports successfully from the grouped layout.
- A simple strict AJ parse → flow → Python compile smoke test succeeds.

The release therefore changes package organisation only; no semantic regression was detected.
