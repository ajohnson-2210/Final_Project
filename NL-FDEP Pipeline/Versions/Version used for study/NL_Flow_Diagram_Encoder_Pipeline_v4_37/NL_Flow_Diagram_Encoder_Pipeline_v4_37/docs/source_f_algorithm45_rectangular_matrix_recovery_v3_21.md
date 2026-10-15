# source_f Algorithm 45 rectangular matrix recovery — v3.21

Source shape:

```text
INPUT A, B (same dimensions R x C)
INIT result as R x C matrix
FOR i from 0 to R-1:
    FOR j from 0 to C-1:
        result[i][j] = A[i][j] + B[i][j]
RETURN result
```

GC223 treats `R` and `C` as source-provided descriptive dimension symbols rather than invented runtime parameters. Because the two inputs are explicitly stated to have the same dimensions, the first supplied matrix is a deterministic shape witness:

- `R` in the guarded row bound becomes `LENGTH OF A`;
- `C` in the guarded column bound becomes `LENGTH OF A[0]`;
- the requested result matrix becomes `CALL create_matrix(LENGTH OF A, LENGTH OF A[0], 0)`.

The temporary zero fill is representation-only. GC223 activates only when the exact matching nested row/column loops contain a direct unconditional `result[i][j]` assignment and the result matrix is returned, proving that every allocated cell is overwritten before the fill value can be observed.

The rule refuses independent `R`/`C` bindings, missing or mismatched dimension loops, conditional/nested writes, source-declared routines, and a target that is not returned. It does not perform general rectangular identifier substitution.

Generated Python for the source_f source uses `len(A)` and `len(A[0])` and preserves the supplied element-wise addition unchanged.
