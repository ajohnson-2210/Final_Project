# NL-FDEP v2.90 release record

## Purpose

v2.90 is a corpus-wide compatibility correction driven by the source_c Algorithm 5 audit. It removes a pipeline-order dependency around the already-supported Python-like `set(...)` constructor surface.

## Changes

- Generalised GC150 so assignment RHS forms `set(value)` and `CALL set(value)` are treated identically.
- The rule accepts either raw `=` or canonical `<-` assignment, so its behaviour does not depend on which generic normalisation pass ran first.
- Both surfaces canonicalise to the existing AJ compatibility helper `CALL to_set(value)`; the compiler continues to emit Python `set(value)`.
- Added generic positive/negative regressions proving that the rule is not tied to source_c, a corpus filename, an algorithm number, a function name, or punctuation-specific content.
- Added the exact source_c Algorithm 5 motivating occurrence as version-controlled audit evidence.
- Preserved the supplied punctuation string exactly, including spaces; v2.90 does not repair or reinterpret source logic.
- AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## Canonical example

```text
values = set(items)
```

becomes:

```text
values <- CALL to_set(items)
```

and compiles to:

```python
values = set(items)
```

## source_c Algorithm 5 classification

```text
status: PASS AFTER CONSERVATIVE SET-CONSTRUCTOR RECOVERY
semantic inference: NO
algorithmic reconstruction: NO
source logic correction: NO
dialect change: NO
```

## Validation

Working-tree validation:

```text
pytest: 376 passed, 3 skipped, 5 subtests passed
unittest: 242 passed, 1 skipped
```

The single unittest skip remains the optional external study-corpus integration check when `AJ_RESEARCH_CORPUS_DIR` is not configured.

The frozen dialect file has the same SHA-256 digest as v2.89.

Extracted-package validation reproduced the same results:

```text
pytest: 376 passed, 3 skipped, 5 subtests passed
unittest: 242 passed, 1 skipped
```
