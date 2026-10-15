# v3.79 — zero-fill consistency pass for implicit allocations

## Change

GC223 no longer assigns a synthetic numeric zero to source_f's same-dimensions matrix-addition result declaration:

```text
INIT result as R x C matrix
```

The source-proven dimensions are unchanged, but the unspecified cell value now canonicalises to:

```text
result <- CALL create_matrix(LENGTH OF A, LENGTH OF A[0], NONE)
```

and compiles to a Python `None`-filled matrix until the source-supplied nested loops assign each result cell.

This release also audits every compatibility rule that emits zero-filled matrix or fixed-array storage. No additional unsupported zero fills were found. Zero remains only where the source explicitly supplies it, including `matrix of 0s`, `matrix filled with 0`, `grid initialized to 0`, `matrix ... initialized with/to 0`, and `array ... initialized to 0`.

The approved consistency rule is therefore:

- source-proven dimensions + no source-proven cell value -> `NONE`;
- source-proven dimensions + explicit zero value -> `0`.

GC160, GC223 and GC224 now follow the first branch for missing fills. GC246, GC249 and generic explicit-zero allocation surfaces remain on the second branch.

## Validation

- 925 pytest passed, 3 skipped, 5 subtests passed.
- 315 unittest passed, 1 skipped.
- AJ v1.1 SHA-256 unchanged: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.
- AJ v1.2 SHA-256 unchanged: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.
