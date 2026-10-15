# source_f Algorithm 46 linked matrix-dimension recovery — v3.22

## Source shape

source_f supplies two linked matrix annotations, `A (M x N)` and `B (N x P)`, requests `C` as an `M x P` matrix, and explicitly provides the full row/column/inner loops, scalar accumulator, multiplication relation, output-cell assignment, and return.

## GC224

GC224 treats `M`, `N`, and `P` only as source-proven shape symbols when the complete guarded structure is present. It represents:

- `M` as `LENGTH OF A`;
- shared `N` as `LENGTH OF B`;
- `P` as `LENGTH OF B[0]`;
- `INIT C as M x P matrix` using `CALL create_matrix(LENGTH OF A, LENGTH OF B[0], 0)`.

The temporary zero fill is representation-only because every allocated `C[i][j]` is directly assigned after the complete inner accumulation. The source-supplied multiplication and index relation are preserved exactly.

GC224 refuses independent dimension bindings, broken shared dimensions, mismatched result or loop bounds, modified accumulation/indexing, conditional result writes, unrelated uses of `M/N/P`, and explicit routine declarations.

## Runtime contract

The caller must supply compatible rectangular 2D matrices matching the stated `M x N` and `N x P` shapes. Because `P` is represented by `LENGTH OF B[0]`, `B` must contain at least one row.

## Classification

**PASS AFTER SOURCE-EVIDENCED LINKED-DIMENSION RECOVERY — TRUSTWORTHY EXECUTABLE**
