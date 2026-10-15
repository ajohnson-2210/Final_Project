# v3.82 — explicit queue abstraction preservation

## Change

v3.82 stops generic compatibility normalisation from exposing a Python list as the canonical representation of a source-provided queue.

When the source explicitly declares `empty queue` / `EMPTY QUEUE`, canonical AJ now preserves that abstraction through ordinary compatibility intrinsics:

```text
queue <- CALL create_queue()
CALL ENQUEUE(queue, value)
item <- CALL DEQUEUE(queue)
CALL queue_is_empty(queue)
CALL queue_size(queue)
```

The Python compiler may still lower those explicit queue operations to a list-backed FIFO implementation (`[]`, `.append(...)`, `.pop(0)`, and `len(...)`) as an implementation detail. Nested `ENQUEUE(target, DEQUEUE(source))` is lowered through a compiler-only temporary so destructive evaluation order remains explicit without inventing a canonical variable.

The same abstraction is preserved for the older anonymous `CREATE Empty Queue` binary-tree traversal recovery and for GC235 queue operations exposed only after one-line structural expansion.

Explicitly list-backed FIFO source remains list-backed. For example, `queue <- EMPTY LIST` or a seeded `LIST [root]` followed by queue-style operations continues to canonicalise through `APPEND`, `REMOVE FIRST ITEM FROM`, and `LENGTH OF`. No queue type is inferred from operation names alone.

A historical flattened-property test using undeclared `node_left` / `node_right` now reaches semantic validation through the queue intrinsics and correctly fails declaration-before-use rather than being masked by list-shaped APPEND operations. This is consistent with the earlier retirement of flattened binary-tree property inference.

## Validation

- 936 pytest passed, 3 skipped, 5 subtests passed.
- 323 unittest passed, 1 skipped.
- AJ v1.1 SHA-256 unchanged: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.
- AJ v1.2 SHA-256 unchanged: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.
