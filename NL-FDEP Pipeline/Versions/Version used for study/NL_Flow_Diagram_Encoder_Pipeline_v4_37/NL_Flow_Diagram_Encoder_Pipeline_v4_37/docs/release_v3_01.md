# NL-FDEP v3.01 release record

## Scope

v3.01 implements the approved bare-error return representation and records source_e Algorithm 33 as an expected executable-correctness failure because the source supplies ordinary `/` where the stated integer-square-root algorithm requires an integer midpoint.

## Production change

- Added `GC204`: exact bare `RETURN ERROR` (case-insensitive) -> `RETURN STRING("ERROR")`.
- The rule is return-position only; it does not create a global `ERROR` constant and does not infer exception semantics.
- No division operator recovery/correction was added.

## source_e 33 audit outcome

- error result: conservatively represented as returned string `"ERROR"`;
- midpoint: source `/` retained exactly;
- automatic conversion to `INTEGER DIVISION`: rejected as algorithmic correction;
- status: **EXPECTED EXECUTABLE-CORRECTNESS FAILURE — SOURCE INTEGER-DIVISION REQUIREMENT NOT SUPPLIED**.

## Dialect

AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## Validation

Working tree:

- pytest: **469 passed, 3 skipped, 5 subtests passed**
- unittest: **255 passed, 1 skipped**

Fresh extraction from packaged ZIP:

- pytest: **469 passed, 3 skipped, 5 subtests passed**
- unittest: **255 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
