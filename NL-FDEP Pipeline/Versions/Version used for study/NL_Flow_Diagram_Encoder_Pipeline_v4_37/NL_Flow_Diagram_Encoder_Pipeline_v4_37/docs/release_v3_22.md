# NL-FDEP v3.22 release record

## Summary

v3.22 adds the approved source_f 46 linked matrix-dimension/result-allocation recovery while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC224 — evidenced linked matrix multiplication dimensions

GC224 recognises only the complete source shape `A (M x N), B (N x P)`, `INIT C as M x P matrix`, matching full `M`, `P`, and shared-`N` loop bounds, explicit zero accumulator, exact `sum += A[i][k] * B[k][j]`, direct `C[i][j] = sum`, and `RETURN C`.

Under those source-proven conditions, annotation-only dimensions are represented as `LENGTH OF A`, `LENGTH OF B`, and `LENGTH OF B[0]`. The output storage is materialised through the existing `create_matrix` intrinsic. No multiplication step, index relation, loop, accumulator, or scalar dimension parameter is invented.

## source_f 46 canonical result

```text
FUNCTION unnamed_function ACCEPTS(A, B)
    C <- CALL create_matrix(LENGTH OF A, LENGTH OF B[0], 0)
    FOR i <- IN RANGE 0 TO (LENGTH OF A-1) + 1 DO
        FOR j <- IN RANGE 0 TO (LENGTH OF B[0]-1) + 1 DO
            sum <- 0
            FOR k <- IN RANGE 0 TO (LENGTH OF B-1) + 1 DO
                sum <- sum + A[i][k] * B[k][j]
            ENDFOR
            C[i][j] <- sum
        ENDFOR
    ENDFOR
    RETURN C
ENDFUNCTION
```

Python RANGE lowering renders the three stop expressions as `len(A)`, `len(B[0])`, and `len(B)`.

AJ_24038155 Dialect v1.1 is unchanged.
