# NL-FDEP v2.95 release record

## Scope

v2.95 records the approved source_c Algorithm 37 expected-failure decision and adds corpus-independent regression evidence for the abstract-array indexed-write non-inference boundary.

No production normalisation, parser, compiler or dialect rule is added. The release deliberately prevents future changes from silently converting empty-array indexed writes into invented append/growth routines.

## source_c 37 classification

```text
status: EXPECTED FAIL — INSUFFICIENT ARRAY GROWTH / STORAGE SEMANTICS
semantic inference: REQUIRED for executable Python
algorithmic/storage reconstruction: REQUIRED
pipeline reconstruction performed: NO
dialect change: NO
```

## Regression evidence

- Exact source_c 37 occurrence remains a safe failure and is not rewritten to append/growth logic.
- A generic empty-array next-index write remains an indexed write and demonstrably raises Python `IndexError` rather than receiving invented growth semantics.
- Explicit source `.append(...)` remains supported.
- Indexed overwrite into explicitly allocated storage remains supported.

## Validation

Working tree:

```text
pytest: 418 passed, 3 skipped, 5 subtests passed
unittest: 242 passed, 1 skipped
```

Fresh extraction of the packaged ZIP:

```text
pytest: 418 passed, 3 skipped, 5 subtests passed
unittest: 242 passed, 1 skipped
AJ v1.1 SHA-256: 0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598
```
