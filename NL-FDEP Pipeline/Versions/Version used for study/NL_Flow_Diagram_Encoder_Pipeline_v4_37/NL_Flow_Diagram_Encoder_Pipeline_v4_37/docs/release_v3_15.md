# NL-FDEP v3.15 release record

## Scope

v3.15 implements the approved recovery identified while auditing source_f Algorithm 35. It adds GC215 for a narrowly evidenced ordered-cache stateful ADT written as a top-level multi-state `INIT` followed by multiple shared-state operations.

## Production change

`pseudocode_profiles.py` adds `EVIDENCED_ORDERED_CACHE_STATEFUL_ADT` processing immediately before strict AJ parsing, after ordinary block, call, membership, length, and assignment recovery has exposed canonical evidence.

GC215 requires an explicit ordered-dictionary initializer, keyed mapping behaviour, a cache-size equality bound, at least two operations sharing the cache state, and source-proven safe contexts for all three recency helpers. It refuses unrelated multi-target INIT forms, unknown call escape, unsafe move/remove/add contexts, nested operation containers, or method assignment to the capacity-like state.

When the proof succeeds, the source is represented using frozen AJ class grammar with:

- neutral `CLASS unnamed_class`;
- constructor parameter copied from the source capacity-like state name;
- `PROPERTY` state for the capacity and dictionary-backed cache;
- source-supplied functions preserved as methods;
- state references qualified through `THIS`;
- existing ordered-mapping intrinsics reused for recency operations.

No numeric capacity default is invented. In particular, capacity zero is not inferred because it is behaviourally invalid for the supplied full-cache condition on the first insertion.

## source_f Algorithm 35

The exact source_f response now compiles into a stateful class whose constructor accepts `capacity`, and whose source-supplied `get` and `put` methods implement the response's ordered-cache behaviour. The conceptual front is MRU and back is LRU, as evidenced by `moveToFront` on access and `removeBack` on eviction.

Classification:

**PASS AFTER EVIDENCED STATEFUL-ADT STRUCTURAL RECOVERY — TRUSTWORTHY EXECUTABLE FOR POSITIVE FIXED CAPACITY**.

## Dialect

AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## Validation

Working tree after the v3.15 change:

- pytest: **608 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`

Fresh extraction from packaged ZIP:

- pytest: **608 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
