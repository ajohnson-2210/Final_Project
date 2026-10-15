# NL-FDEP v3.24 release record

## Summary

v3.24 implements the approved source_c 35 source-surface recovery while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC226 — trailing explanatory parenthetical comment

GC226 does not treat parentheses generally as comments. It activates only when an assignment already has a complete `empty <collection>` right-hand side and the trailing parenthetical begins with the explanatory markers `or` or `for`.

For example:

```text
order = empty list (or a doubly linked list to maintain access order)
```

is represented as the executable initialiser `order = empty list`, with the parenthesised suffix detached as non-executable commentary before literal and collection parsing. This prevents the explanatory word `list` inside the comment from being reinterpreted as constructor syntax. Grouped arithmetic, function calls, and non-comment parentheticals remain untouched.

## Existing source_c LRU recovery surface acceptance

The existing GC161 LRU class recovery already contains the source-evidenced constructor/state/method representation. v3.24 allows that recogniser to accept either already-canonical `FUNCTION ... ACCEPTS(...)` headers or the legacy source_c spellings `FUNCTION get(key):` and `FUNCTION put(key, value):`. No LRU operation is added or inferred.

## source_c 35 canonical result

```text
CLASS LRUCache ACCEPTS(capacity)
    cache <- EMPTY DICTIONARY
    order <- EMPTY LIST

    FUNCTION get ACCEPTS(key)
        IF key NOT IN cache THEN
            RETURN -1
        ENDIF
        CALL remove_from_list(order, key)
        CALL insert_front(order, key)
        RETURN cache[key]
    ENDFUNCTION

    FUNCTION put ACCEPTS(key, value)
        IF key IN cache THEN
            cache[key] <- value
            CALL remove_from_list(order, key)
            CALL insert_front(order, key)
        ELSE
            IF LENGTH OF order >= capacity THEN
                lruKey <- order[-1]
                CALL remove_last_from_list(order)
                CALL remove_key(cache, lruKey)
            ENDIF
            CALL insert_front(order, key)
            cache[key] <- value
        ENDIF
    ENDFUNCTION
ENDCLASS
```

For positive capacities, the generated Python preserves the source-supplied MRU-front/LRU-back behaviour.

AJ_24038155 Dialect v1.1 is unchanged.

## Validation

- targeted source_c/source_f LRU regression: **15 passed**
- full pytest: **676 passed, 3 skipped, 5 subtests passed**
- full unittest: **260 passed, 1 skipped**
