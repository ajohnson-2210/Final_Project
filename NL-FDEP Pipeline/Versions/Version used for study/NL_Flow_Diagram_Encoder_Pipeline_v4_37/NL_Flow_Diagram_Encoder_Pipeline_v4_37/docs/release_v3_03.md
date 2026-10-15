# NL-FDEP v3.03 release record

## Scope

v3.03 implements the approved source_e Algorithm 43 function-shaped output recovery.

## Production change

- Added `GC206`: standalone balanced single-expression `PRINT(expression)` -> `OUTPUT expression`.
- Reused the existing `OUTPUT`-only Python f-string renderer for mixed literal/identifier message chains.
- No AJ `to_string(...)` or Python `str(...)` cast is inserted.
- No Tower-of-Hanoi logic, recursion, or type information is invented.

## source_e 43 audit outcome

- source algorithm: complete;
- source output surface: `PRINT(...)`;
- canonical AJ output: `OUTPUT ...`;
- Python message rendering: f-string where the existing narrow output-renderer boundary applies;
- status: **PASS AFTER CONSERVATIVE FUNCTION-SHAPED OUTPUT RECOVERY AND OUTPUT-FORMATTING LOWERING**.

## Dialect

AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## Validation

Working tree:

- pytest: **491 passed, 3 skipped, 5 subtests passed**
- unittest: **255 passed, 1 skipped**

Fresh extraction from packaged ZIP:

- pytest: **491 passed, 3 skipped, 5 subtests passed**
- unittest: **255 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
