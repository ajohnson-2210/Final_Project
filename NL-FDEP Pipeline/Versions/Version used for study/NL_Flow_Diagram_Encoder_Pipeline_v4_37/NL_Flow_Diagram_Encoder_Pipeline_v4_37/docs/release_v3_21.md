# NL-FDEP v3.21 release record

## Summary

v3.21 adds the approved source_f 45 rectangular-dimension/matrix-allocation recovery while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC223 — evidenced rectangular matrix allocation

GC223 recognises only an unnamed top-level source that explicitly states two matrix inputs share dimensions `R x C`, explicitly requests an `R x C` result matrix, traverses the matching full row and column ranges, directly overwrites every `result[i][j]`, and returns that result matrix.

Under those source-proven conditions, `R` and `C` are annotation-only shape symbols and are represented directly as `LENGTH OF A` and `LENGTH OF A[0]`. The result matrix is materialised through the existing `create_matrix` compatibility intrinsic with a temporary zero fill. The fill is semantically unobservable because the guard proves every cell is overwritten before return. No synthetic dimension parameters or arithmetic are invented.

## source_f 45 canonical result

```text
FUNCTION unnamed_function ACCEPTS(A, B)
    result <- CALL create_matrix(LENGTH OF A, LENGTH OF A[0], 0)
    FOR i <- IN RANGE 0 TO (LENGTH OF A-1) + 1 DO
        FOR j <- IN RANGE 0 TO (LENGTH OF A[0]-1) + 1 DO
            result[i][j] <- A[i][j] + B[i][j]
        ENDFOR
    ENDFOR
    RETURN result
ENDFUNCTION
```

Python range lowering canonicalises the compiler-introduced inclusive-bound offset to `range(0, len(A))` and `range(0, len(A[0]))`.

## Validation

- targeted source_f 45 / source_f 42 / source_f 41 regression bundle: 20 passed
- rectangular behavioural checks: all shapes 1x1 through 5x5 passed
- pytest: 654 passed, 3 skipped, 5 subtests passed
- unittest: 260 passed, 1 skipped
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`

AJ_24038155 Dialect v1.1 is unchanged.
