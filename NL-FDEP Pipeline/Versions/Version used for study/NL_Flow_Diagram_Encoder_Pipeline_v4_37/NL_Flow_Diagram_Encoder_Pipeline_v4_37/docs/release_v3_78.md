# v3.78 — GC224 unspecified matrix fill preserves absence

## Change

GC224 still recognises only the complete, source-evidenced linked matrix-multiplication shape `A (M x N), B (N x P)` with matching result dimensions and loops. The dimension recovery is unchanged.

The result declaration:

```text
INIT C as M x P matrix
```

now canonicalises to:

```text
C <- CALL create_matrix(LENGTH OF A, LENGTH OF B[0], NONE)
```

and compiles to a Python matrix whose allocated cells initially contain `None`. This preserves the fact that the source specifies dimensions but does not specify an initial data value.

If the source explicitly says `initialized with 0`, `initialised with 0`, `initialized to 0`, or `initialised to 0`, GC224 preserves that zero and emits `create_matrix(..., 0)`.

The source-supplied accumulator initialisation `sum = 0` remains unchanged.

## Validation

- 921 pytest passed, 3 skipped, 5 subtests passed.
- 315 unittest passed, 1 skipped.
- AJ v1.1 SHA-256 unchanged: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.
- AJ v1.2 SHA-256 unchanged: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.
