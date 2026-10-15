# v3.83 — explicit deque abstraction preservation

## Change

v3.83 removes the remaining compatibility-layer representation leak for source-provided double-ended queues.

When the source explicitly provides a deque abstraction, canonical AJ now preserves it through ordinary compatibility calls:

```text
deque <- CALL create_deque()
CALL deque_push_back(deque, value)
front <- CALL deque_front(deque)
back <- CALL deque_back(deque)
CALL deque_pop_front(deque)
CALL deque_pop_back(deque)
CALL deque_is_empty(deque)
CALL deque_size(deque)
```

The Python compiler may still use a list as the implementation detail:

```python
deque = []
deque.append(value)
front = deque[0]
back = deque[-1]
deque.pop(0)
deque.pop(-1)
len(deque)
```

This applies only when deque backing is explicitly evidenced by source forms such as `empty deque`, `empty DoubleEndedQueue`, `EMPTY DEQUE`, or a zero-argument `Deque()` / `DoubleEndedQueue()` constructor. Method names alone do not establish deque type.

GC237 now keeps evidenced `REMOVE FRONT`, `REMOVE BACK`, and `ADD BACK` operations as deque intrinsics instead of routing them through AJ list primitives. source_c Algorithm 28 and source_d Algorithm 28 therefore retain the source's deque abstraction while compiling to the same sliding-window behaviour.

GC136 is intentionally unchanged. A source that explicitly declares `deque <- EMPTY LIST` and then uses front/back shorthand remains list-backed; v3.83 does not relabel explicit list storage as a deque.

No AJ v1.2 grammar change is required: all deque compatibility operations use existing ordinary `CALL` syntax.

## Validation

- 940 pytest passed, 3 skipped, 5 subtests passed.
- 323 unittest passed, 1 skipped.
- AJ v1.1 SHA-256 unchanged: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.
- AJ v1.2 SHA-256 unchanged: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.
