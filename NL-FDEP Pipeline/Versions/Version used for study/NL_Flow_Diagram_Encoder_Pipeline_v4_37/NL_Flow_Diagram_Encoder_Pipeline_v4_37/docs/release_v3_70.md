# Release v3.70 — GC160 uninitialised matrix storage uses NONE fill

v3.70 narrows GC160's handling of the exact direct-assignment surface `target <- matrix of size rows x cols` when the source supplies dimensions but no initial cell value.

The source-provided dimensions remain deterministic and are represented through the existing matrix-allocation intrinsic as:

```text
target <- CALL create_matrix(rows, cols, NONE)
```

The generated Python therefore allocates writable slots without inventing a numeric value:

```python
target = [[None for _ in range(cols)] for _ in range(rows)]
```

This preserves the source's matrix dimensions while representing the absence of an initial cell value with AJ v1.1 `NONE` / Python `None`.

Explicit fill evidence is unchanged. For example, `target <- matrix of size rows x cols initialized with 0` continues to canonicalise to `CALL create_matrix(rows, cols, 0)` and compiles to a zero-filled matrix. Existing exact `rows * cols matrix of 0s` handling is also unchanged.

Validation:

- focused GC160/matrix regression gate: 116 passed;
- full pytest gate: 899 passed, 3 skipped, 5 subtests passed;
- unittest gate: 303 passed, 1 skipped;
- frozen AJ_24038155 Dialect v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

No frozen grammar, parser syntax, or explicit-fill semantics change in v3.70.
