# v3.90 — source_f Algorithm 27 source-arithmetic expected-failure audit

v3.90 does not change normalisation or compiler semantics. It strengthens the audit evidence for source_f Algorithm 27, whose source explicitly uses ordinary `/` in the `N/2` matrix-rotation loop bound.

The pipeline continues to preserve `/` exactly and therefore intentionally exposes the Python `range(... float ...)` failure. No `/` -> `DIV` / `//` compatibility exception is introduced.

The audit now records the counterfactual diagnosis required by the study: if, and only if, the source arithmetic is changed to integer division, the otherwise unchanged rotation algorithm correctly rotates representative 2x2, 3x3, and 4x4 matrices. This demonstrates that the failure is attributable to the source arithmetic rather than to the surrounding rotation logic, while keeping the production pipeline source-faithful.

See `docs/source_f_algorithm27_source_division_expected_failure_audit_v3_90.md` and `tests/test_source_f_algorithm27_square_dimension_division_v3_11.py`.
