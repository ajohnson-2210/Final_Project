# NL-FDEP v2.98 release record

## Scope

v2.98 generalises the pre-existing function-shaped arithmetic canonicalisation so raw `MOD(...)` / `FLOOR(...)` surfaces and their already-`CALL`-prefixed equivalents converge on the same AJ operators before generic free-call prefixing can make them unparsable.

The motivating occurrence is source_e Algorithm 2 (decimal to binary). The implementation is corpus-wide and contains no model/file/algorithm/routine-specific condition.

## Behaviour

- `MOD(a, b)` / `CALL MOD(a, b)` / `MODULUS(a, b)` / `CALL MODULUS(a, b)` -> `(a MODULUS b)`.
- `FLOOR(a / b)` / `CALL FLOOR(a / b)` -> `(a INTEGER DIVISION b)` under the existing floor-of-division restriction.
- Existing numeric-to-string recovery remains responsible for converting a modulus result prepended to an evidenced string.
- Member methods and unsupported arities are not reclassified.

## Audit classification

source_e 2: **PASS AFTER CONSERVATIVE FUNCTION-SHAPED ARITHMETIC RECOVERY**.

- semantic inference: NO NEW SEMANTIC INFERENCE
- algorithmic reconstruction: NO
- source logic correction: NO
- dialect change: NO

## Validation

Working tree:

- pytest: **446 passed, 3 skipped, 5 subtests passed**
- unittest: **255 passed, 1 skipped**

Fresh extraction from packaged ZIP:

- pytest: **446 passed, 3 skipped, 5 subtests passed**
- unittest: **255 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
