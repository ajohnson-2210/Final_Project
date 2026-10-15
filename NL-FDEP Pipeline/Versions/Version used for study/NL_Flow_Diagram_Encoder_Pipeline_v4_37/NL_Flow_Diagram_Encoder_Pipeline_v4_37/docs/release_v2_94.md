# NL-FDEP v2.94 release record

## Purpose

v2.94 is a corpus-wide constructor-surface normalisation driven by the source_c Algorithm 34 audit. It preserves an explicitly supplied Python-like `list(expression)` operation through frozen AJ v1.1 by canonicalising it to the existing compatibility helper `CALL to_list(expression)`.

## Changes

- Added GC201 for free one-argument `list(expression)` and `CALL list(expression)` surfaces.
- GC201 uses balanced-parenthesis scanning so nested explicit argument expressions are preserved intact.
- Member methods such as `object.list(...)` are not reclassified.
- Zero-argument and multi-argument `list` calls are not guessed.
- Constructor-looking text inside strings/comments is untouched.
- Added corpus-independent positive/negative regressions plus the exact source_c Algorithm 34 motivating occurrence.
- No model/file/algorithm/function-name condition was added to implementation logic.
- AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## source_c Algorithm 34 classification

```text
status: PASS AFTER CANONICAL AJ LIST-CONSTRUCTOR SURFACE NORMALISATION
semantic inference: NO
algorithmic reconstruction: NO
control-flow change: NO
dialect change: NO
```

## Validation

Working-tree validation:

```text
pytest: 414 passed, 3 skipped, 5 subtests passed
unittest: 242 passed, 1 skipped
```

The single unittest skip is the optional external study-corpus integration check when `AJ_RESEARCH_CORPUS_DIR` is not configured.

Frozen AJ_24038155 Dialect v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

Extracted-package validation reproduced the same results:

```text
pytest: 414 passed, 3 skipped, 5 subtests passed
unittest: 242 passed, 1 skipped
```
