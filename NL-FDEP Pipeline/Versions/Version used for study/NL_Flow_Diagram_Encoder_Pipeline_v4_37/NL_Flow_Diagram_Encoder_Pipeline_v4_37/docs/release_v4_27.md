# NL-FDEP v4.27 — behavioural oracle execution contract correction

Pipeline: **NL-FDEP v4.27**  
Dialect: **AJ_24038155 Dialect v1.4 (unchanged)**  
Scoring rubric: **v1.1 (unchanged)**  
Scoring schema: **v1.4 (unchanged)**  
Common Test Design: **v1.1 (50 suites / 113 tests, unchanged)**

## Purpose

v4.27 corrects the behavioural execution contract exposed when the packaged Common Tests v1.1 were first run against the frozen Strict benchmark. The v4.26 batch could parse and compile the benchmark but the oracle runner executed title-bearing `Algorithm n Baseline Python code.txt` files verbatim. A descriptive first-line title could therefore become a Python `SyntaxError`, and that infrastructure error could incorrectly be learned as the expected behaviour. At the same time, Strict AJ intrinsic calls such as `LOWERCASE(...)` and `CHARACTERS_OF(...)` could remain unresolved in generated Python.

## Reference-oracle execution

- The frozen baseline Python file is never modified.
- The raw file SHA-256 remains the provenance anchor.
- If the first non-blank line exactly matches the packaged suite's `algorithm_title`, that one line may be commented only in an in-memory/temporary execution view.
- No unmatched prose is silently stripped or rewritten.
- Reference validation records raw syntax validity, executable-view syntax validity, whether normalisation was applied, the exact rule, and both raw/execution hashes.
- A reference source with no syntax-valid executable view is not accepted as an oracle.
- On non-`ERROR_BEHAVIOUR` tests, a reference runtime/infrastructure error is not adopted as expected behaviour merely because the subprocess completed.
- `ERROR_BEHAVIOUR` tests may still derive an expected exception/return code from the trusted reference where that is the behaviour being exercised.

## Strict AJ compiler execution fixes

- Recognised AJ intrinsics `LOWERCASE` and `UPPERCASE` are lowered case-insensitively to Python string operations.
- `CHARACTERS_OF(value)` is lowered to `list(value)`.
- `QUIT` and legacy `STOP` now lower to `raise SystemExit`, which remains deterministic under the study harness' isolated `python -S` execution. Generated Python no longer depends on the optional `site.quit`/`site.exit` helpers.
- The trusted-reference temporary execution view supplies controlled `quit`/`exit` equivalents for legacy frozen Python sources while leaving those sources byte-for-byte unchanged.

## Benchmark policy

Baseline Benchmark Folder processing remains fixed to `AJ_DIALECT_STRICT`. Experimental inputs retain their independently selected profile. The packaged Common Tests remain the same 50 suites / 113 executable tests used in v4.26.

## Validation

- 1,238 pytest tests passed, 3 skipped, 5 subtests passed.
- 383 unittest tests passed, 1 skipped.
- New regressions cover exact-title reference execution normalisation, fail-closed unmatched reference syntax, non-error oracle runtime-fault rejection, error-behaviour oracle derivation, Strict uppercase intrinsic lowering, and isolated deterministic termination.
