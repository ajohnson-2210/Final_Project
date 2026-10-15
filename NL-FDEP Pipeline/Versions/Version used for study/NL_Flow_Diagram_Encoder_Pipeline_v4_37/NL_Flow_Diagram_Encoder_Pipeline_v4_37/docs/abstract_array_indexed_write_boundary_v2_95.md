# Abstract array indexed-write non-inference boundary — v2.95

An indexed assignment is not equivalent to an append operation.

The compatibility layer may preserve explicit source operations such as:

```text
items.append(value)
```

as canonical AJ `APPEND value TO items`, because the source itself supplies append semantics.

It may also preserve indexed overwrite into storage that the source has explicitly allocated, for example a one-element list followed by `data[0] <- value`.

However, when a source declares an empty abstract array/list and then writes to the next non-existent index, the pipeline must not invent dynamic-growth behaviour such as:

```python
if index == len(array):
    array.append(value)
else:
    array[index] = value
```

unless that behaviour is itself supplied by the pseudocode or by an explicitly defined/imported primitive. Doing so would add storage-management semantics that are absent from the source.

This boundary is corpus-wide and independent of model, file, algorithm number, class name and variable name.
