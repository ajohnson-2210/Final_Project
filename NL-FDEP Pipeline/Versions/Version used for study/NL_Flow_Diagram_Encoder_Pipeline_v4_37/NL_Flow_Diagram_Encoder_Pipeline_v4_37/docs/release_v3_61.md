# Release v3.61 — retire GC159 generic linked-list flattened-property inference

## Scope

This release removes GC159's generic conversion of a valid underscored identifier such as `current_next` into `current.next` merely because `current` is assigned from a `head` parameter.

## Retired GC159 behaviour

For example:

```text
FUNCTION inspect ACCEPTS(head)
    current <- head
    current_next <- 5
    OUTPUT current_next
    RETURN head
ENDFUNCTION
```

now preserves `current_next` exactly as written and compiles it as an ordinary Python local variable.

AJ v1.1 permits `_` inside identifiers. Neither `current <- head` nor the spelling `current_next` independently establishes that the source denotes a `.next` member on an object named `current`.

Explicit source member access such as `current.next` remains unchanged.

## Preserved Floyd recoveries

The historical Floyd cycle-detection recoveries remain separately gated for the two retained corpus vocabularies:

- `slow` / `fast`;
- `tortoise` / `hare`.

These paths preserve their previous `*_next -> .next` behaviour without restoring the retired generic `head` + `*_next` inference. Other names such as `current_next` remain ordinary identifiers.

## Validation

- focused GC159 linked-list boundary/Floyd gate: 6 passed.
- in-tree pytest: 869 passed, 3 skipped, 5 subtests passed.
- in-tree unittest: 282 passed, 1 skipped.
- frozen dialect SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.
