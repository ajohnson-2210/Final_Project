# NL-FDEP v4.22 project structure

The grouped project layout introduced in v4.14 remains unchanged. v4.22 enriches the existing study/scoring metadata; no new runtime top-level folder is required.

Key v4.22 files:

- `study components/study_batch.py` — records declared descriptive G2 suite metadata in `test_suite_evidence.json`.
- `study components/scoring_engine.py` — combines declared suite metadata with runtime test evidence to create the descriptive G2 profile.
- `study components/study_analysis.py` — exports descriptive G2 fields to aggregate JSON/CSV tables.
- `study components/human_review.py` — displays G2 evidence and captures reviewer assessment.
- `study components/adjudication.py` — preserves optional human G2 adjudication without affecting numerical scores.
- `study components/study_rubric.py` — rubric v1.1 with descriptive G2 schema requirements; C1-P4 unchanged.
- `docs/scoring_rubric_v1_1.json` — current JSON representation of rubric v1.1 under pipeline v4.22.
- `docs/common_test_design_v1_1.md` — descriptive common-test design.
- `docs/common_test_suite_manifest_v1_1.json` — 50-algorithm / 113-test pack metadata.
- `examples/study_tests_template.json` — test-spec schema v1.2 example.
