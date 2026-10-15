# NL-FDEP v3.45 release record

## Scope

v3.45 implements the approved source_d Algorithm 41 square zero-grid allocation recovery while leaving frozen AJ_24038155 Dialect v1.1 unchanged.

## GC246 explicit square zero-grid allocation

An exact direct assignment of the form:

```text
board <- N x N grid initialized to 0
```

is represented through the existing matrix-construction compatibility intrinsic as:

```text
board <- CALL create_matrix(N, N, 0)
```

The rule acts only when both dimensions are the same single source identifier and the source explicitly supplies a zero fill. Rectangular grids, expression dimensions, non-zero fills, missing initialisers and broader prose remain outside the rule. No matrix algorithm, parser construct, compiler primitive or dialect feature is added.

GC246 composes with v3.44 GC245: source_d Algorithm 41 now reaches strict AJ parsing and deterministic Python compilation. Its next independent failure remains visible at the explicit `Copy(board)` call, which v3.45 does not interpret or repair.

## Validation

- targeted GC246 regression/refusal-boundary tests: 5 passed;
- full pytest suite: 777 passed, 3 skipped, 5 subtests passed;
- full unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 777 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
