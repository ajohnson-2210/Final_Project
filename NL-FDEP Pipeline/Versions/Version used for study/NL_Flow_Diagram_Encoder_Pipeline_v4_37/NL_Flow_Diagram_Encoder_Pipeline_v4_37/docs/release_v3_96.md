# v3.96 — FOR EACH rebinding semantics and explicit REVERSE mutation

v3.96 removes compiler-invented collection write-back from `FOR EACH` loops.

AJ `FOR EACH item IN collection DO ... ENDFOR` binds the loop variable for each
iteration. Reassigning that loop variable does not itself state that the
corresponding element of the source collection must be replaced. Previous
compiler output detected assignments to the loop variable, switched to
`enumerate(...)`, and emitted an extra `collection[index] = item` assignment.
That additional mutation was not present in the source semantics.

## Compiler change

Canonical AJ such as:

```text
FOR EACH value IN values DO
    value <- 0
ENDFOR
```

now compiles directly to:

```python
for value in values:
    value = 0
```

with no generated `enumerate(...)` index and no implicit assignment back into
`values`. Collection mutation must be explicit in the source operation.

## REVERSE preservation

The compatibility normaliser previously lowered standalone imperative
`REVERSE target` to `target <- CALL reverse_value(target)`, which creates a new
reversed value. The removed FOR EACH write-back had been masking that mismatch
for aliased rows such as source_a's matrix-rotation `REVERSE Row`.

Standalone `REVERSE target` now lowers to:

```text
CALL reverse_list(target)
```

which compiles to Python's in-place `.reverse()` operation. This preserves the
source-authored mutation without relying on FOR EACH to invent collection
replacement. Indexed forms such as `REVERSE matrix[i]` likewise compile to
`matrix[i].reverse()`.

## Dialect impact

None. AJ dialect v1.1 and v1.2 source documents are unchanged.

- AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
- AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`

## Validation

985 pytest passed, 3 skipped, 5 subtests passed; 329 unittest passed, 1 skipped.
