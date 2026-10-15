# source_f Algorithm 35 — evidenced ordered-cache stateful ADT recovery — v3.15

## Source occurrence

```text
INIT capacity, cache = orderedDict()

FUNCTION get(key):
    IF key in cache:
        moveToFront(cache, key)
        RETURN cache[key]
    ELSE:
        RETURN null

FUNCTION put(key, value):
    IF key in cache:
        moveToFront(cache, key)
        cache[key] = value
    ELSE:
        IF length(cache) == capacity:
            removeBack(cache)

        addToFront(cache, key, value)
```

## Evidence decision

The original task requires a fixed-capacity memory buffer that evicts the least recently accessed item when full. In the response, `capacity` and `cache` are persistent names declared before multiple operations; `cache` is explicitly an `orderedDict`, and both `get` and `put` act on that shared state.

The initial audit rejected automatic execution because `INIT capacity, cache = orderedDict()` does not supply a numeric value for `capacity`. Behavioural testing then established that defaulting `capacity` to zero is not valid: the first insertion would satisfy `LENGTH OF cache == capacity` and attempt to remove an item from an empty cache. The approved interpretation is therefore constructor-supplied fixed capacity, not zero initialisation.

The ordering direction is also source-evidenced. Accessed/existing keys are moved to the front, while the back is removed on a full insertion. Therefore conceptual front is MRU and conceptual back is LRU.

## GC215 recovery

GC215 is deliberately not a generic multi-target `INIT` split. It requires all of the following after ordinary compatibility normalisation:

1. the first executable line is `INIT limit, cache = CALL orderedDict()`;
2. the remaining program consists of at least two top-level functions plus comments/blank lines;
3. every operation references the shared cache state and at least one operation reads the limit state;
4. the cache is used as a keyed mapping (`key IN cache` and indexed access);
5. the source contains `LENGTH OF cache == limit`;
6. `moveToFront(cache, key)` occurs only inside a proven `key IN cache` true branch;
7. `removeBack(cache)` occurs only inside a proven full-capacity branch;
8. `addToFront(cache, key, value)` occurs only inside the corresponding absent-key branch;
9. no unknown free call is permitted to escape or mutate the ordered-cache state;
10. the limit state is not assigned a synthetic/default value inside the operations.

When those conditions hold, GC215 emits frozen AJ class grammar using a neutral class name:

```text
CLASS unnamed_class
    PROPERTY capacity
    PROPERTY cache AS DICTIONARY

    CONSTRUCTOR ACCEPTS(capacity)
        PROPERTY THIS.capacity <- capacity
        PROPERTY THIS.cache <- EMPTY DICTIONARY
    ENDCONSTRUCTOR

    METHOD get ACCEPTS(key)
        ...
    ENDMETHOD

    METHOD put ACCEPTS(key, value)
        ...
    ENDMETHOD
ENDCLASS
```

No semantic class name is invented. The source-supplied `get` and `put` names and signatures are preserved.

## Ordered-map lowering

No new LRU algorithm is added to the compiler. GC215 reuses existing ordered-mapping intrinsics already present in the pipeline:

- conceptual `moveToFront(cache, key)` -> physical `move_key_to_back(cache, key)`, because Python insertion-order dictionaries represent the MRU end at the physical back;
- conceptual `removeBack(cache)` -> physical `remove_first_mapping(cache)`, removing the oldest mapping;
- conceptual `addToFront(cache, key, value)` -> keyed dictionary insertion, which appends a new key at the physical MRU end.

The source itself proves that `addToFront` is reached only when the key is absent, so keyed insertion also performs the required ordering effect.

## Behavioural verification

The exact recovered source_f source is compiled and exercised against an independent reference LRU implementation across deterministic random mixed `get`/`put` sequences for positive capacities 1 through 5. The recovered implementation preserves both values and LRU-to-MRU ordering.

Capacity zero is explicitly not synthesised or claimed as a valid default.

## Classification

**PASS AFTER EVIDENCED STATEFUL-ADT STRUCTURAL RECOVERY — TRUSTWORTHY EXECUTABLE FOR POSITIVE FIXED CAPACITY**

AJ_24038155 Dialect v1.1 remains frozen and unchanged.
