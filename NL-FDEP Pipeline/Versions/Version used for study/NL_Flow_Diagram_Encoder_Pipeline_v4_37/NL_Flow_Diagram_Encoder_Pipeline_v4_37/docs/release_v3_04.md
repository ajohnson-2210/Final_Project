# NL-FDEP v3.04 release record

## Scope

v3.04 records the approved source_e Algorithm 47 expected-failure boundary.

## Production change

None. No normaliser, parser, compiler, or dialect semantics are changed.

## Semantic-integrity boundary

- Explicit `[]` remains `EMPTY LIST` and Python `[]`.
- Later keyed access does not trigger an inferred list-to-dictionary conversion.
- Explicit dictionary source remains dictionary-backed.
- The source_e 47 example therefore remains an expected runtime failure under its own inconsistent source collection semantics rather than being silently corrected.

## source_e 47 audit outcome

- source declaration: explicit empty list;
- later usage/example: mapping-style keyed access and dictionary-shaped expected result;
- pipeline response: preserve the explicit list;
- status: **EXPECTED FAIL — SOURCE COLLECTION SEMANTICS ARE INTERNALLY INCONSISTENT**.

## Dialect

AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## Validation

Working tree:

- pytest: **495 passed, 3 skipped, 5 subtests passed**
- unittest: **255 passed, 1 skipped**

Fresh extraction from packaged ZIP:

- pytest: **495 passed, 3 skipped, 5 subtests passed**
- unittest: **255 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
