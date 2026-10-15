# NL-FDEP v3.02 release record

## Scope

v3.02 implements the approved source_e Algorithm 40 class-terminator surface recovery.

## Production change

- Added `GC205`: standalone case-insensitive `END CLASS` -> `ENDCLASS`.
- Existing GC202 nested stack-push recovery and GC203 frozen-AJ explicit-class canonicalisation are reused unchanged.
- No queue algorithm, class state, constructor, or method semantics are invented by GC205.

## source_e 40 audit outcome

- source algorithm: complete;
- source terminator: `END CLASS`;
- canonical AJ terminator: `ENDCLASS`;
- status: **PASS AFTER CONSERVATIVE CLASS-TERMINATOR SURFACE NORMALISATION**.

## Dialect

AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## Validation

Working tree:

- pytest: **478 passed, 3 skipped, 5 subtests passed**
- unittest: **255 passed, 1 skipped**

Fresh extraction from packaged ZIP:

- pytest: **478 passed, 3 skipped, 5 subtests passed**
- unittest: **255 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
