# v3.80 — generic explicit-stack abstraction preservation

## Change

GC160 no longer rewrites an explicitly declared `empty stack` / `EMPTY STACK` as `EMPTY LIST`.

An explicit stack declaration now canonicalises to the existing abstract stack constructor:

```text
stack <- CALL create_stack()
```

Source-evidenced stack operations remain stack operations in canonical AJ:

```text
CALL PUSH(value, stack)
CALL POP(stack)
CALL stack_is_empty(stack)
```

The Python compiler may still lower those explicit stack abstractions to a list-backed implementation (`[]`, `.append(...)`, `.pop(-1)`, and `len(...) == 0`) as an implementation detail.

This also updates explicit stateful-class recovery so stack-valued state remains untyped in canonical AJ rather than being declared `AS LIST`. For source_c Algorithm 40, the canonical class therefore uses:

```text
PROPERTY stack1
PROPERTY stack2

CONSTRUCTOR ACCEPTS()
    PROPERTY THIS.stack1 <- CALL create_stack()
    PROPERTY THIS.stack2 <- CALL create_stack()
ENDCONSTRUCTOR
```

and its methods use `PUSH`, `POP`, and `stack_is_empty` rather than `APPEND`, member `.pop()`, or `LENGTH OF` as canonical stack semantics.

Explicit `EMPTY LIST` sources are unchanged and continue to use list-backed AJ operations. GC121's separate array-backed stack remains an expected failure when its source omits array capacity.

## Validation

- 929 pytest passed, 3 skipped, 5 subtests passed.
- 319 unittest passed, 1 skipped.
- AJ v1.1 SHA-256 unchanged: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.
- AJ v1.2 SHA-256 unchanged: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.
