# NL-FDEP v4.28 — benchmark execution and Python representation correction

Pipeline: **NL-FDEP v4.28**  
Dialect: **AJ_24038155 Dialect v1.4 (unchanged)**  
Scoring rubric: **v1.1 (unchanged)**  
Scoring schema: **v1.4 (unchanged)**  
Common Test Design: **v1.1 (50 suites / 113 tests, unchanged)**

## Purpose

v4.28 is a narrow correction derived from a full inspection of the frozen 50-algorithm Baselines corpus after the v4.27 calibration run. It does not alter the benchmark pseudocode, frozen reference Python, Common Test executable arrays, scoring criteria, or AJ language standard.

## Controlled reference-heading recognition

Six packaged Common Test `algorithm_title` values are historical truncations of the longer first-line descriptive headings in the corresponding frozen reference Python files. v4.27 accepted only exact title equality, leaving those otherwise executable references `REFERENCE_NOT_EVALUATED`.

v4.28 permits a second fail-closed execution-view rule only when all of the following hold:

- the packaged `algorithm_title` is at least 80 characters long;
- the frozen reference first non-blank line starts exactly with that title;
- the frozen heading is longer than the packaged title; and
- commenting that one heading line produces syntax-valid Python.

The frozen source is never modified. Raw source SHA-256 remains the provenance anchor. The execution metadata records the declared title, full reference heading, execution-view SHA-256 and the exact rule `COMMENT_PREFIX_MATCHED_TRUNCATED_TEST_SUITE_ALGORITHM_TITLE`. Short or unrelated prefixes remain rejected.

## `RAISE SystemExit` control flow

A source-authored `RAISE SystemExit` is now lowered to `raise SystemExit`. It is no longer wrapped as `raise Exception(SystemExit)`. This preserves termination semantics exposed by Algorithm 32 while leaving ordinary string/data `RAISE` expressions on the historical generic-exception path.

## Protected AJ method names and Python name mangling

AJ strict reserved-identifier escaping can produce method names beginning `__reserved_keyword__`. Python privately name-mangles such declarations inside classes, while the canonical external call retains the visible escaped spelling. v4.28 publishes a same-spelling class alias after class definition using the actual mangled method object. This fixes Python representation without changing AJ identifiers or rewriting arbitrary external member calls.

## Deliberately preserved residual differences

The Baselines audit also found behavioural differences that are not safely attributable to these infrastructure defects. v4.28 deliberately leaves them visible, including unresolved source-specific punctuation sentinels, output whitespace/placeholder differences, Algorithm 32's frozen loop-variable discrepancy, Algorithm 39's later `remove_cycle` behaviour, and malformed frozen reference Python such as Algorithm 25. No benchmark source is rewritten to improve a score.

## Benchmark policy

Baseline Benchmark Folder processing remains fixed to `AJ_DIALECT_STRICT`. Experimental inputs retain their independently selected profile. Packaged Common Tests v1.1 remain the canonical resource and baseline-local tests remain fallback only.

## Validation

- 1,242 pytest tests passed, 3 skipped, 5 subtests passed.
- 383 unittest tests passed, 1 skipped.
- Packaged Common Test validation remains 50/50 suites and 113/113 tests.
- A controlled local rerun of the uploaded frozen Baselines corpus produced 48/50 evaluated calibrations; this rerun is diagnostic only and is environment-dependent for optional reference dependencies.
