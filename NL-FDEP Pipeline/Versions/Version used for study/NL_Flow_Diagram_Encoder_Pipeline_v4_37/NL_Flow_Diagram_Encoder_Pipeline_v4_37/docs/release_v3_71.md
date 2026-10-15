# Release v3.71 — GC175 multi-part output preserves message semantics

v3.71 narrows GC175's exact source_a Algorithm 9 recovery for the source output:

```text
OUTPUT "Found at position", i
```

The previous compatibility form represented those output components as tuple data:

```text
OUTPUT TUPLE(STRING("Found at position"), i)
```

which compiled to Python tuple formatting. The canonical output now uses AJ v1.1's existing string-placeholder syntax:

```text
OUTPUT STRING("Found at position {i}")
```

and the Python renderer emits an f-string:

```python
print(f"Found at position {i}")
```

This preserves the source's intended single message rather than changing it into tuple data. Genuine source `TUPLE(...)` values remain unchanged.

Validation:

- focused output regression gate: 14 passed;
- full pytest gate: 899 passed, 3 skipped, 5 subtests passed;
- unittest gate: 303 passed, 1 skipped;
- frozen AJ_24038155 Dialect v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

No frozen grammar change in v3.71.
