# NL-FDEP v4.15 project structure

The v4.14 grouped folder structure is retained. v4.15 removes bundled research corpus fixtures from `tests/`. Research corpora are external study data and are not part of the implementation package.

Root files:

- `pycharm_runner.py`
- `README.md`
- `requirements.txt`
- `VERSION`
- `pytest.ini`

Grouped folders include `manifests/`, `flow diagram components/`, `parser components/`, `compiler components/`, `pipeline components/`, `study components/`, `cli components/`, `examples/`, `docs/`, and `tests/`.

There is intentionally no bundled `tests/corpora/` directory in v4.15.
