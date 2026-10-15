# Release v3.58 — retire GC159 generic flattened-property inference

## Scope

This release removes the remaining generic semantic inference from GC159's nested `otherX` iterator handling.

## Retired GC159 behaviour

A nested loop such as:

```text
FOR EACH item IN items DO
    FOR EACH otherItem IN items DO
        OUTPUT otherItem_value
    ENDFOR
ENDFOR
```

no longer causes `otherItem_value` to be rewritten as `otherItem.value`. The same applies to `item_value` and arbitrary suffixes discovered from the iterator names.

AJ v1.1 permits `_` inside identifiers, so a flattened spelling is already a valid identifier and does not prove member access. Nested iterator names provide no independent object/property evidence.

## Preserved behaviour

GC159's separate specialised object-context recoveries remain unchanged in this release and can be audited independently. Explicit source member access such as `otherItem.value` is also preserved. v3.57's retirement of automatic self-exclusion remains in force.

## Validation

- focused GC159/adjacent regression gate: 9 passed.
- in-tree pytest: 858 passed, 3 skipped, 5 subtests passed.
- in-tree unittest: 271 passed, 1 skipped.
- frozen dialect SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.
