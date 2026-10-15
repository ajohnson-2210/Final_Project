# Negative-infinity representation recovery — v2.99

GC151 now accepts equivalent explicit negative-infinity assignment surfaces:

```text
x = -infinity
x <- -infinity
x = NEGATIVE_INFINITY
x <- NEGATIVE_INFINITY
```

case-insensitively, and canonicalises them to:

```text
x <- CALL negative_infinity()
```

The rule is deliberately assignment-scoped. It does not rewrite member access, longer identifiers, or arbitrary bare reads such as `RETURN NEGATIVE_INFINITY`.

This is a source-shape-independent extension of the existing negative-infinity compatibility representation, not a new mathematical or algorithmic inference.
