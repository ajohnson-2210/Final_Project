# Corpus-wide set-constructor surface recovery — v2.90

## Rule

A Python-like set constructor used as an assignment RHS may occur before or after generic call-prefix normalisation:

```text
x = set(value)
x <- set(value)
x = CALL set(value)
x <- CALL set(value)
```

All four forms represent the same already-supported operation and canonicalise to:

```text
x <- CALL to_set(value)
```

The compiler continues to emit:

```python
x = set(value)
```

## Boundary

The rule is source-shape independent but intentionally does not reinterpret unrelated names or member methods. Examples such as `dataset(value)` and `object.set(value)` are not the free built-in set-constructor surface and are left to the ordinary call/member-call rules.

No algorithmic content is invented and no collection contents are altered.
