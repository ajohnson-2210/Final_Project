# NL-FDEP v2.92 release record

## Purpose

v2.92 is a corpus-wide compatibility correction driven by the source_c Algorithm 28 audit. It removes an ordering limitation in Python-like list `.append(...)` canonicalisation when the explicit append value contains nested expressions.

## Changes

- Added GC200: balanced standalone `name.append(expression)` canonicalisation when `name` has explicit LIST evidence.
- Preserved the existing GC033 path for simple append arguments.
- Added negative controls proving nested `.append(...)` on a receiver without list evidence is not reclassified.
- Added nested-call, nested-index and quoted-parenthesis regressions.
- Added the exact source_c Algorithm 28 occurrence as motivating audit evidence and a behavioural regression.
- No algorithm-specific/model-specific/file-specific implementation condition was introduced.
- AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## source_c Algorithm 28 classification

```text
status: PASS AFTER CANONICAL AJ LIST-SYNTAX NORMALISATION
semantic inference: NO
algorithmic reconstruction: NO
control-flow change: NO
dialect change: NO
```

## Validation

Working-tree validation:

```text
pytest: 393 passed, 3 skipped, 5 subtests passed
unittest: 242 passed, 1 skipped
```

The single unittest skip, if present, is the optional external study-corpus integration check when `AJ_RESEARCH_CORPUS_DIR` is not configured.

Frozen AJ_24038155 Dialect v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

Extracted-package validation reproduced the same results:

```text
pytest: 393 passed, 3 skipped, 5 subtests passed
unittest: 242 passed, 1 skipped
```
