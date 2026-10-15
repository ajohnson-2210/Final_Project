# v3.81 — GC244 explicit Stack() abstraction preservation

## Change

GC244 no longer rewrites an evidenced zero-argument `Stack()` constructor used as class state to `EMPTY LIST`.

When an explicit class constructor assigns a member from `Stack()` and the same member is used through stack operations, the canonical form now preserves the stack abstraction:

```text
self.stack <- CALL create_stack()
CALL PUSH(value, self.stack)
CALL POP(self.stack)
CALL stack_is_empty(self.stack)
```

For source_d Algorithm 40, `Stack()` state therefore remains stack state in canonical AJ. The Python compiler may still lower the explicit stack abstraction to a list-backed implementation (`[]`, `.append(...)`, `.pop(-1)`, and `len(...) == 0`) as an implementation detail.

GC244 remains contextual: local `Stack()` calls, non-zero-argument `Stack(...)` calls, constructor members with no stack-usage evidence, later member rebinds, and explicit list sources are not reclassified by this rule.

This aligns the explicit `Stack()` constructor path with v3.76 GC124 (`CREATE Stack`) and v3.80 GC160 (`empty stack`) while preserving GC121's separate expected-failure boundary for an array-backed stack whose capacity is missing.

## Validation

- 932 pytest passed, 3 skipped, 5 subtests passed.
- 319 unittest passed, 1 skipped.
- AJ v1.1 SHA-256 unchanged: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.
- AJ v1.2 SHA-256 unchanged: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.
