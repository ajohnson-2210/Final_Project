# v3.87 explicit orderedDict compiler lowering

v3.87 fixes the remaining execution gap for an explicitly authored zero-argument `orderedDict()` constructor without changing its canonical AJ spelling.

## Source-preserving constructor lowering

An explicit source constructor such as:

```text
cache <- orderedDict()
```

continues to canonicalise as:

```text
cache <- CALL orderedDict()
```

The compatibility layer does not rename the constructor as `create_ordered_dictionary()` or weaken it to `EMPTY DICTIONARY`.

Previously, the Python compiler emitted the unknown call `orderedDict()`, which raised `NameError`. v3.87 lowers the explicit compatibility constructor to Python's corresponding ordered mapping:

```python
cache = __import__('collections').OrderedDict()
```

This preserves the stronger evidence carried by the named source constructor and keeps ordering semantics explicit at runtime.

## Deliberately unchanged boundaries

The generic phrase `ordered dictionary` remains the v3.86 abstraction:

```text
CALL create_ordered_dictionary()
```

and continues to use normal Python `{}` backing because Python dictionaries preserve insertion order. Plain `empty dictionary` / hash-map forms remain plain dictionaries. No LRU policy, eviction operation, key movement, or other algorithmic behaviour is added by this compiler lowering.

Case variants of the explicit zero-argument `orderedDict()` compatibility constructor are accepted by the compiler only after the AJ parser has represented them as a call; non-zero-argument calls are not rewritten.

## Validation

- 958 pytest passed, 3 skipped, 5 subtests passed.
- 323 unittest passed, 1 skipped.
- Historical AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.
- Active AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.
