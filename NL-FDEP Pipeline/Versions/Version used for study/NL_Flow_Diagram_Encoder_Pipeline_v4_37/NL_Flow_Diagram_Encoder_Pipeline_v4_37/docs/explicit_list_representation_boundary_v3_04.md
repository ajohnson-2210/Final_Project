# Explicit list representation boundary — v3.04

When source pseudocode explicitly initialises a collection with `[]` or an equivalent empty-list surface, that is positive evidence for list semantics. Downstream operations must not silently retype that collection to a dictionary merely because some later access pattern would work better with mapping storage.

Generic boundary:

```text
x = []
x[key] = value
```

remains an explicit-list program. If `key` is incompatible with Python list indexing, the generated Python may fail. The pipeline does not repair that source inconsistency by replacing the list with a dictionary.

Conversely, explicit dictionary source such as `x = empty dictionary` continues to compile as dictionary storage.

This is a semantic-integrity guard, not a new recovery rule.
