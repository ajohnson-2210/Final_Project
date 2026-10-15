# GC209 / GC210 — collection conversion and default-empty join surface recovery

## GC209 — free one-argument `array(value)`

A free source call with exactly one balanced top-level argument:

```text
array(value)
```

is canonicalised to:

```text
CALL to_list(value)
```

This reuses the existing AJ/Python mutable-list conversion and does not add a new runtime dependency. The rule does not inspect model name, corpus file, algorithm number, wrapper name, or variable names.

Excluded forms include `.array(...)`, `array()`, `array(a, b)`, quoted text and comments.

## GC210 — free one-argument `join(collection)`

A free source call with exactly one balanced top-level argument:

```text
join(collection)
```

is canonicalised to:

```text
JOIN(collection, EMPTY STRING)
```

The empty separator is the explicitly approved conventional representation for this one-argument surface. Native/two-argument AJ `JOIN(collection, separator)` is left unchanged.

Excluded forms include `.join(...)`, `join()`, `join(a, b)` as a default-empty recovery, three-or-more-argument forms, quoted text and comments.

## Semantic boundary

Both rules recover source representation only. They do not reconstruct an algorithm, infer collection contents, invent imports/helpers, or alter control flow. AJ_24038155 Dialect v1.1 remains frozen.
