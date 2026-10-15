# NL-FDEP v3.08 release record

## Scope

v3.08 implements the approved source_f Algorithm 13 collection-conversion and default-empty-join compatibility recovery.

## Production changes

### GC209

Free one-argument:

```text
array(value)
```

becomes:

```text
CALL to_list(value)
```

using the existing list-conversion runtime mapping.

### GC210

Free one-argument:

```text
join(collection)
```

becomes:

```text
JOIN(collection, EMPTY STRING)
```

so Python lowers it to an empty-string separator join.

Both rules use balanced single-argument handling and exclude member methods, other arities, quoted text and comments. Existing two-argument AJ `JOIN` remains unchanged.

## source_f Algorithm 13

The exact corpus occurrence now compiles to the equivalent of:

```python
chars = list(s)
...
return ''.join(chars)
```

and the supplied manual swap/reversal logic is otherwise unchanged.

## Audit boundary

- semantic inference: **LIMITED REPRESENTATION INFERENCE**
- algorithmic reconstruction: **NO**
- source control-flow correction: **NO**
- invented helper/import: **NO**
- dialect change: **NO**

## Dialect

AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## Validation

Working tree:

- pytest: **546 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**

Fresh extraction from packaged ZIP:

- pytest: **546 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
