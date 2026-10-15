# NL-FDEP v2.93 release record

## Purpose

v2.93 is a corpus-wide static-semantic integrity correction driven by the source_c Algorithm 29 audit. It prevents abstract result placeholders from producing a false executable pass when they are used as direct unbound values.

## Changes

- Activated a conservative direct subset of AJ's declared/assigned-before-read static semantic rule.
- Direct bare identifier reads in assignment/property-assignment RHS, `RETURN` and `OUTPUT` now require a visible binding.
- Parameters, prior assignments and enclosing-scope bindings remain valid.
- Preserved the existing legacy `NULL` compatibility sentinel; canonical AJ v1.1 continues to use `NONE`.
- Deliberately did not introduce full compound-expression/control-flow definite-assignment analysis in this release.
- Reclassified the existing source_c Algorithm 29 evidence as an expected static-semantic failure.
- Updated the historical generic regression that previously asserted a successful parse of the abstract classifier placeholders.
- Added corpus-independent positive/negative semantic regressions plus the exact motivating study occurrence.
- No model/file/algorithm/function-name condition was added to implementation logic.
- AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## source_c Algorithm 29 classification

```text
status: EXPECTED FAIL — ABSTRACT ALGORITHM / UNBOUND RESULT DEPENDENCIES
failure stage: STATIC_SEMANTIC_ANALYSIS
semantic inference required for execution: YES
algorithmic reconstruction: YES
complete Python generation: NO
dialect change: NO
```

## Validation

Working-tree validation:

```text
pytest: 401 passed, 3 skipped, 5 subtests passed
unittest: 242 passed, 1 skipped
```

The single unittest skip is the optional external study-corpus integration check when `AJ_RESEARCH_CORPUS_DIR` is not configured.

Frozen AJ_24038155 Dialect v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

Extracted-package validation reproduced the same results:

```text
pytest: 401 passed, 3 skipped, 5 subtests passed
unittest: 242 passed, 1 skipped
```
