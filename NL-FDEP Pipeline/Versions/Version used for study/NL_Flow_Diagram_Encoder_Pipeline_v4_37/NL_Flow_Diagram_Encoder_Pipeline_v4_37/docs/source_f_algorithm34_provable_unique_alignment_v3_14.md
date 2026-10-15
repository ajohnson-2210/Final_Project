# source_f Algorithm 34 — provable uniqueness semantic alignment — v3.14

## Source occurrence

```text
INPUT list1, list2

set1 = set(list1)
result = []

FOR item in list2:
    IF item in set1 AND item not in result:
        result.append(item)

RETURN unique(result)
```

## Source proof

The source explicitly initialises `result` as empty and appends `item` only under the guard `item not in result`. Therefore, after every loop iteration, `result` contains no duplicate values.

The final `unique(result)` abstraction names a postcondition the source has already established. Implementing an undefined `unique` helper is unnecessary, while converting through a set could introduce ordering behaviour not supplied by the source.

## v3.14 alignment

GC214 therefore aligns the final operation to:

```text
RETURN result
```

only after mechanically proving the uniqueness invariant from the same routine. The source-created first-occurrence order from `list2` is preserved.

The rule is guarded against arbitrary `unique(x)` calls, unguarded or mismatched appends, repeated appends under one guard, guards outside repeating loops, rebinding, indexed/insert writes, alias escape, and unknown-call escape.

## Classification

**PASS AFTER PROVABLE SEMANTIC ALIGNMENT — TRUSTWORTHY EXECUTABLE**

No new deduplication algorithm is invented, no set/list round-trip is introduced, and AJ_24038155 Dialect v1.1 is unchanged.
