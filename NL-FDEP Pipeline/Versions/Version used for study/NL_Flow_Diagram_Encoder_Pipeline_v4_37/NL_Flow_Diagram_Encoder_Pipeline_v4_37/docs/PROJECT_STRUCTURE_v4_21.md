# NL-FDEP v4.21 project structure

The grouped project layout introduced in v4.14 remains unchanged. v4.21 adds study/test metadata handling within existing compiler and study components; no new runtime top-level folder is required.

Key v4.21 files:

- `compiler components/aj_test_harness.py` — deterministic seed/environment-aware behavioural execution.
- `study components/baseline_benchmark.py` — reference execution and common-test oracle creation.
- `study components/study_batch.py` — writes `test_suite_evidence.json` for each processed algorithm.
- `study components/scoring_engine.py` — G2 and category-level behavioural metrics.
- `study components/study_rubric.py` — scoring rubric v1.1.
- `docs/scoring_rubric_v1_1.json` — frozen JSON representation of rubric v1.1.
- `examples/study_tests_template.json` — v1.1 common-test template.
