# Free list-constructor surface recovery — v2.94

## Purpose

v2.94 adds a corpus-wide syntax-surface normalisation for the Python-like built-in list constructor. AJ_24038155 Dialect v1.1 reserves `LIST` as a language keyword, so a free call written as `list(expression)` cannot be preserved verbatim as an ordinary AJ function identifier.

This is representational normalisation only. It does not infer a collection type, create data, alter control flow, or reconstruct an algorithm.

## General rule GC201

Either source surface:

```text
list(expression)
CALL list(expression)
```

canonicalises to:

```text
CALL to_list(expression)
```

The existing compiler lowers `CALL to_list(expression)` to Python:

```python
list(expression)
```

## Safeguards

GC201 is independent of model, filename, algorithm number and surrounding function name.

It applies only when:

- the call is a free call, not `object.list(...)`;
- exactly one top-level argument is supplied;
- parentheses are balanced;
- constructor-looking text is not inside a string or comment.

Nested calls, indexing and grouping inside the single explicit argument are preserved by a balanced scan.

GC201 deliberately does not guess the meaning of `list()` with no argument or `list(a, b)` with multiple arguments. Those surfaces remain unresolved.

## Dialect status

AJ_24038155 Dialect v1.1 is frozen. This rule changes only the generic-compatibility normaliser and does not alter the dialect grammar or semantics.
