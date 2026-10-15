# v3.86 source-abstraction constructor preservation

v3.86 removes the remaining generic constructor/conversion cases found in the collection-abstraction audit where canonical AJ renamed an explicitly supplied source abstraction as a different collection kind.

## GC209 — `array(value)` remains ARRAY

Previously, free one-argument `array(value)` was represented as `CALL to_list(value)`. That exposed the Python backing representation in canonical AJ even though the source explicitly requested an array conversion.

v3.86 canonicalises the same tightly gated free single-argument surface as:

```text
CALL to_array(value)
```

The Python compiler lowers `CALL to_array(value)` to `list(value)` because a mutable Python list is the deterministic backing used by this compiler. The LIST is therefore an implementation detail only. Member `.array(...)` calls, zero/multi-argument calls, comments, and quoted text remain outside GC209.

## GC030 — `ordered dictionary` remains ordered

Previously, the source phrase `ordered dictionary` canonicalised to `EMPTY DICTIONARY`, discarding the explicit ordering guarantee. v3.86 now represents it as:

```text
CALL create_ordered_dictionary()
```

The compiler lowers this intrinsic to a Python dictionary. Modern Python dictionaries preserve insertion order, while canonical AJ retains the stronger source-level ordered-mapping abstraction. Plain `empty dictionary`, `empty map`, and `empty hash map` remain `EMPTY DICTIONARY`.

The existing LRU compatibility rule accepts either its historical plain-dictionary fixture or the new source-faithful ordered-dictionary intrinsic; no LRU policy or missing algorithmic operation is invented.

## Consistency audit

The same audit confirmed that the following paths are already abstraction-faithful and were intentionally left unchanged:

- `list(value)` -> `CALL to_list(value)`;
- `set(value)` / `ConvertToSet(value)` -> `CALL to_set(value)`;
- explicit empty list/set/dictionary/hash-map declarations retain their own collection kinds;
- explicit STACK/QUEUE/DEQUE abstractions continue to use their dedicated intrinsics where evidence-gated rules apply;
- named `Stack()` / `Queue()` calls outside those evidence-gated recovery contexts remain named constructor calls rather than being relabelled as LIST or ARRAY;
- previously approved set-extension compatibility lowering is unchanged.

Historical v3.08 documentation records the behaviour that existed in that release; v3.86 supersedes its GC209 list-conversion representation for current releases.

## Validation

- 954 pytest passed, 3 skipped, 5 subtests passed.
- 323 unittest passed, 1 skipped.
- Historical AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.
- Active AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.
