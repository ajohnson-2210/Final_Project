# v3.89 — retire GC214; `unique(...)` preserves SET return semantics

v3.89 applies the user-confirmed interpretation that an exact one-argument `unique(collection)` operation denotes SET conversion.

## Semantic correction

GC214 previously removed a final `unique(result)` call when the routine mechanically proved that the values already stored in `result` were duplicate-free. That value-level proof is insufficient once `unique(...)` is defined to return a SET: deleting the call changes the collection type from SET to LIST.

GC214 is therefore retired from the active generic-compatibility sequence. GC222 now handles every exact one-identifier `unique(name)` form, including cases where the input list is already value-unique:

```text
RETURN unique(result)
```

becomes:

```text
RETURN CALL to_set(result)
```

and compiles to Python:

```python
return set(result)
```

The source_f unsorted-list intersection case therefore preserves its explicit SET return type even though its guarded append logic already prevents duplicate values.

## Scope

This release does not broaden `unique` matching. Member calls, zero/multi-argument calls, and unrelated collection operations remain outside GC222. AJ dialect files are unchanged.

## Validation

- 963 pytest passed, 3 skipped, 5 subtests passed.
- 323 unittest passed, 1 skipped.
- AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
- AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`
