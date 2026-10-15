# NL-FDEP v3.48 release record

## Scope

v3.48 implements the approved source_d Algorithm 45 explicit rectangular zero-filled matrix-allocation spelling while leaving frozen AJ_24038155 Dialect v1.1 unchanged.

## GC249 explicit rectangular matrix zero fill

When a direct assignment explicitly supplies two simple dimensions and the phrase:

```text
rows x cols matrix filled with 0
```

GC249 represents it through the pipeline's existing matrix-construction intrinsic:

```text
CALL create_matrix(rows, cols, 0)
```

For source_d Algorithm 45 this gives:

```text
C <- CALL create_matrix(rows, cols, 0)
```

which lowers deterministically to independent Python rows:

```python
C = [[0 for _ in range(cols)] for _ in range(rows)]
```

The rule preserves rectangular dimensions exactly and does not infer dimensions from another matrix. It refuses expression dimensions, non-zero or missing fills, `grid` spellings, and prose. No matrix, parser, compiler, or dialect semantics are added.

## Validation

- targeted GC249 regression and refusal-boundary tests: 5 passed;
- full pytest suite: 793 passed, 3 skipped, 5 subtests passed;
- full unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 793 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
