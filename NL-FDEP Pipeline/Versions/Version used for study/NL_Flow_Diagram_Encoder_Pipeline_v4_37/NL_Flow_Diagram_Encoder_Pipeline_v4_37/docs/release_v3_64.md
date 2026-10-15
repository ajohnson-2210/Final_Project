# Release v3.64 — retire GC159 Floyd flattened-property inference

## Scope

This release removes GC159's remaining Floyd-specific conversion of valid underscored identifiers such as `slow_next`, `fast_next`, `tortoise_next`, and `hare_next` into member access such as `slow.next`, `fast.next`, `tortoise.next`, and `hare.next` merely because state variables are initialised from `head`.

## Retired GC159 behaviour

The compatibility layer no longer treats the names `slow`/`fast` or `tortoise`/`hare` as evidence that an underscored identifier denotes a linked-list `next` property. It also no longer rewrites a mixed surface such as `fast_next.next` into `fast.next.next`.

AJ_24038155 Dialect v1.1 permits underscores in identifiers and represents member access explicitly with `.`. Therefore the following spellings remain distinct:

- `slow_next` — ordinary identifier;
- `slow.next` — explicit member access;
- `fast_next.next` — member `next` of the object referenced by identifier `fast_next`;
- `fast.next.next` — explicit two-step member access from `fast`.

Historical flattened Floyd fixtures that read undeclared identifiers such as `slow_next` now correctly reach the existing declaration-before-use semantic boundary instead of being silently repaired into a different algorithm.

## Preserved behaviour

Explicit source member access remains unchanged. Sources that actually contain `slow.next`, `fast.next.next`, `tortoise.next`, or `hare.next.next` continue to parse and compile as member access. Generic `current_next` retirement from v3.61 remains in force, as do the later GC159/GC146 retirement boundaries.

## Validation

- focused Floyd/GC159 retirement gate: 8 passed;
- full pytest gate: 880 passed, 3 skipped, 5 subtests passed;
- full unittest gate: 293 passed, 1 skipped;
- frozen AJ_24038155 Dialect v1.1 SHA-256 unchanged: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

No parser, compiler, intrinsic, or frozen AJ_24038155 Dialect v1.1 semantics change in v3.64.
