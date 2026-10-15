# NL-FDEP v3.27 release record

## Scope

v3.27 implements the approved source_e 26 seeded list-backed queue compatibility recovery while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC229 — seeded list-backed queue operations

GC229 recognises a receiver that the source explicitly initialises from a non-empty list literal, represented after earlier canonicalisation as `CALL list_value(...)`, when that same receiver is explicitly used by free `DEQUEUE(receiver)` and/or `ENQUEUE(receiver, value)` operations. Bare source-call forms and already-prefixed `CALL` forms are accepted.

The recovery reuses existing AJ operations only:

- `DEQUEUE(receiver)` -> `REMOVE FIRST ITEM FROM receiver`
- `ENQUEUE(receiver, value)` -> `APPEND value TO receiver`

No queue type is inferred from a variable name. Seeded lists without queue operations and queue operations on receivers lacking explicit list-backing evidence remain untouched.

## source_e 26

The exact level-order traversal source now preserves `queue = [root]`, FIFO dequeue, child enqueue, per-level grouping, and the source loop structure. The generated Python uses `queue.pop(0)` and `queue.append(...)` and produces the expected breadth-first levels for non-null binary-tree roots.

## Validation

The release is accepted only after the targeted GC229 tests, the full pytest suite, the unittest suite, a fresh-extraction rerun, and the frozen-dialect hash check pass.
