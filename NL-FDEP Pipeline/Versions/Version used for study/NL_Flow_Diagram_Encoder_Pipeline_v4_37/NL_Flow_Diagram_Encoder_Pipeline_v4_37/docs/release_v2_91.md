# NL-FDEP v2.91 release record

## Purpose

v2.91 is a corpus-wide compatibility correction driven by the source_c Algorithm 17 audit. It removes an ordering dependency between parenthesised multi-value `RETURN`/`OUTPUT` surfaces and generic free-call prefixing.

## Changes

- Generalised GC080 to accept both `RETURN a, b` and `RETURN (a, b)` as the same explicit tuple return.
- Generalised GC081 to accept both `OUTPUT a, b` and `OUTPUT (a, b)` as the same explicit tuple output.
- Added depth-aware outer-parenthesis handling so grouped single expressions and nested call arguments are not misclassified as tuple values.
- Added `RETURN` to GC083's protected AJ keyword set so it cannot become `CALL RETURN(...)` during new processing.
- Retained the older GC152 `CALL RETURN(...)` recovery solely for backwards-compatible already-mangled input.
- Added generic positive and negative regressions independent of source/model/function names.
- Added the exact source_c Algorithm 17 occurrence as motivating audit evidence and a behavioural regression.
- AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## source_c Algorithm 17 classification

```text
status: PASS AFTER CONSERVATIVE TUPLE-RETURN RECOVERY
semantic inference: NO
algorithmic reconstruction: NO
control-flow change: NO
dialect change: NO
```

## Validation

Working-tree validation:

```text
pytest: 386 passed, 3 skipped, 5 subtests passed
unittest: 242 passed, 1 skipped
```

The single unittest skip remains the optional external study-corpus integration check when `AJ_RESEARCH_CORPUS_DIR` is not configured.

The frozen AJ_24038155 Dialect v1.1 file has the same SHA-256 digest as v2.90: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

Extracted-package validation reproduced the same results:

```text
pytest: 386 passed, 3 skipped, 5 subtests passed
unittest: 242 passed, 1 skipped
```
