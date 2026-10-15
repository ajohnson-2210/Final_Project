# NL-FDEP v2.89 release record

## Purpose

v2.89 is a corpus-wide compatibility correction driven by the source_c Algorithm 1 audit. It resolves `ASCII(x)` as a representational overstatement of the existing `CHAR(x)` compatibility representation and preserves reserved-keyword identifier escaping.

## Changes

- Generalised the existing GC157 surface recovery from only `CALL ASCII(x)` to both `ASCII(x)` and `CALL ASCII(x)`.
- Retained the existing reversible `__reserved_keyword__` identifier escape for identifiers colliding with case-insensitive AJ keywords, including `char` versus `CHAR`.
- Removed the legacy `areAnagrams` function-name-specific `CALL character(...) -> CHAR(...)` fallback.
- Added the exact source_c Algorithm 1 motivating occurrence as audit regression evidence.
- Added generic source-shape, case, reserved-identifier and negative-control regressions.
- AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## Canonical example

```text
FOR EACH char IN text
    value = ASCII(char)
```

becomes:

```text
FOR EACH __reserved_keyword__char IN text DO
    value <- CHAR(__reserved_keyword__char)
ENDFOR
```

and compiles using the existing compatibility lowering to Python `ord(...)`.

## Validation

Working-tree validation:

```text
pytest: 368 passed, 3 skipped, 5 subtests passed
unittest: 242 passed, 1 skipped
```

The single unittest skip remains the optional external study-corpus integration check when `AJ_RESEARCH_CORPUS_DIR` is not configured. Extracted-package validation reproduced the same results:

```text
pytest: 368 passed, 3 skipped, 5 subtests passed
unittest: 242 passed, 1 skipped
```
