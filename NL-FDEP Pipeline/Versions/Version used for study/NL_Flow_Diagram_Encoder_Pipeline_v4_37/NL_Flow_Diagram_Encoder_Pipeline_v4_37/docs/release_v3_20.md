# NL-FDEP v3.20 release record

## Summary

v3.20 completes the approved source_f 42 recovery while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC220 — indexed write overrides bare-brace name hint

A simple receiver initialised with bare `{}` is resolved to `EMPTY DICTIONARY` when the same receiver is later used as an indexed assignment target. This stronger operation evidence overrides weak set-like identifier hints such as `seen`. Membership or `.add(...)` use alone does not trigger the rule.

## GC221 — evidenced balanced `.add(...)` on a list

A standalone `receiver.add(nested_expression)` is recovered as AJ `APPEND` only when `receiver` is independently proven list-backed by explicit source initialisation. Balanced-parenthesis scanning preserves nested arguments. Existing downstream tuple and MIN/MAX canonicalisation then handles the recovered expression; no new value or operation is invented.

## GC222 — exact `unique(name)` deduplication intrinsic

GC214 still runs first and removes `unique(result)` only when uniqueness is already source-proven. If an exact one-argument `CALL unique(name)` remains, GC222 routes it to the existing `CALL to_set(name)` compatibility intrinsic, which compiles to Python `set(name)`. This preserves the explicitly requested deduplication operation and does not infer ordering or a list return type.

## source_f 42 canonical result

```text
FUNCTION unnamed_function ACCEPTS(arr, target)
    seen <- EMPTY DICTIONARY
    pairs <- EMPTY LIST
    FOR EACH num IN arr DO
        comp <- target - num
        IF comp IN seen THEN
            APPEND TUPLE(CALL min(num, comp), CALL max(num, comp)) TO pairs
        ENDIF
        seen[num] <- BOOLEAN(TRUE)
    ENDFOR
    RETURN CALL to_set(pairs)
ENDFUNCTION
```

Python lowering returns `set(pairs)`.

## Validation

- source_f 42 exhaustive behavioural comparison: 35,154 small-array/target cases, zero mismatches
- pytest: 646 passed, 3 skipped, 5 subtests passed
- unittest: 260 passed, 1 skipped
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`

AJ_24038155 Dialect v1.1 is unchanged.
