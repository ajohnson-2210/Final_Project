# Release v3.55 — evidenced collection query/access dispatch

## Scope

This release contains the approved evidence-gating of GC045-GC048 plus the constructor-instance evidence propagation required to preserve explicitly established class collection state.

## GC045-GC048 evidence gating

The historical method spellings no longer establish receiver type by themselves:

- GC045 `.size()` requires list/set/dictionary/queue/deque/stack evidence.
- GC046 `.front()` requires list/queue/deque evidence.
- GC047 `.back()` requires list/stack/deque evidence.
- GC048 `.isEmpty()` requires list/set/dictionary/queue/deque/stack evidence.

The rules keep their existing target meanings and historical audit IDs.  Unproven receivers remain member calls.

## Constructor instance-member evidence

An explicit collection construction assigned to `self.<member>` or `THIS.<member>` inside a constructor now establishes that member's collection evidence in the immediately enclosing class scope.  Sibling methods may consume that evidence.

Safeguards:

- bare constructor locals are not promoted;
- method-local direct rebinds invalidate inherited evidence only in that method;
- evidence does not leak between classes;
- a constructor appearing later does not forward-prove earlier methods;
- operation spelling still never creates type evidence.

This restores source_d algorithm 40's constructor-backed two-stack queue while preserving the tightened refusal of an unproven nested `indexer.front()` call.

## Validation

- focused collection/query regression gate: 31 passed.
- in-tree pytest: 847 passed, 3 skipped, 5 subtests passed.
- in-tree unittest: 260 passed, 1 skipped.
- frozen dialect SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

Fresh-extraction rerun: 847 pytest passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped; frozen dialect hash unchanged.
