# v3.88 — GC215 preserves ordered-cache abstractions and stops before invented Python

v3.88 corrects the source_f Algorithm 35 ordered-cache recovery boundary and supersedes the specialised `collections.OrderedDict` lowering introduced in v3.87.

## Structural recovery retained

The source shape

```text
INIT capacity, cache = orderedDict()

FUNCTION get(key):
    ...

FUNCTION put(key, value):
    ...
```

still provides sufficient evidence for GC215 to recover persistent object state. The capacity-like name has no source-supplied value, so it becomes the constructor parameter. The cache has an explicit dictionary initialiser, so it becomes internally initialised key/value dictionary state:

```text
CLASS unnamed_class
    PROPERTY capacity
    PROPERTY cache AS DICTIONARY

    CONSTRUCTOR ACCEPTS(capacity)
        PROPERTY THIS.capacity <- capacity
        PROPERTY THIS.cache <- EMPTY DICTIONARY
    ENDCONSTRUCTOR
    ...
ENDCLASS
```

No numeric capacity default is invented and `cache` is not turned into a mutable default argument.

## Ordering helpers remain opaque

Earlier GC215 versions interpreted the source-authored helpers

```text
moveToFront(cache, key)
removeBack(cache)
addToFront(cache, key, value)
```

as concrete LRU/dictionary operations. That supplied executable semantics not present in the source.

v3.88 instead preserves them after state qualification:

```text
CALL moveToFront(THIS.cache, key)
CALL removeBack(THIS.cache)
CALL addToFront(THIS.cache, key, value)
```

The recovered class therefore remains valid canonical AJ, but Python compilation intentionally returns an expected-failure result with no generated source while any of these helpers is unresolved. If the source provides explicit top-level FUNCTION definitions for those names, the guard no longer blocks compilation. Unrelated external calls remain permitted as before.

## `orderedDict()` dictionary interpretation

An explicit zero-argument `orderedDict()` remains source-faithful in canonical AJ:

```text
CALL orderedDict()
```

but its Python backing is now an ordinary key/value dictionary:

```python
{}
```

rather than `collections.OrderedDict()`. Any ordering behaviour must come from source-authored operations, not from silently selecting a specialised Python container. The generic `ordered dictionary` compatibility intrinsic and plain dictionaries continue to use `{}` backing.

## Validation

- pytest: **961 passed, 3 skipped, 5 subtests passed**
- unittest: **323 passed, 1 skipped**
- historical AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
- active AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`
