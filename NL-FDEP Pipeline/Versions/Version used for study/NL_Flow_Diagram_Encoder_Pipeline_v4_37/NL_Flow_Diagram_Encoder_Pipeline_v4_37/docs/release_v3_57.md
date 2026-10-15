# Release v3.57 — retire GC159 automatic self-exclusion

## Scope

This release removes one semantic invention from GC159 while retaining its separate flattened-property surface recovery unchanged.

## Retired GC159 behaviour

A nested iterator whose name begins with `other`, when iterating over the same collection as an outer iterator, no longer causes compatibility normalisation to insert an exclusion guard such as:

```text
IF otherItem != item THEN
    ...
ENDIF
```

The iterator name is not evidence that the algorithm intends pairwise comparison excluding the current element.

## Preserved GC159 behaviour

The existing flattened-property recovery remains available in v3.57. For the recognised nested-iteration surface, forms such as `otherItem_value` may still canonicalise to `otherItem.value`. This behaviour is intentionally left for separate review rather than bundled into the self-exclusion correction.

If the source explicitly contains `IF otherItem != item THEN`, that condition remains present; v3.57 only prevents GC159 from inventing it.

## Validation

- focused GC159 regression gate: 4 passed.
- in-tree pytest: 855 passed, 3 skipped, 5 subtests passed.
- in-tree unittest: 268 passed, 1 skipped.
- frozen dialect SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

Fresh-extraction rerun: 855 pytest passed, 3 skipped, 5 subtests passed; 268 unittest passed, 1 skipped; frozen dialect hash unchanged.
