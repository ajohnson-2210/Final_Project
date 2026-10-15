# Release v3.76 — GC124 preserves the abstract two-stack queue representation

## Problem

source_a Algorithm 40 explicitly creates two stacks and manipulates them only through stack operations:

```text
CREATE Stack1
CREATE Stack2

ENQUEUE(Item)
    PUSH Item onto Stack1

DEQUEUE()
    IF Stack2 is empty THEN
        WHILE Stack1 is not empty
            PUSH POP(Stack1) onto Stack2
        ENDWHILE
    ENDIF

    OUTPUT POP(Stack2)
```

GC124 previously canonicalised both stack creations as `EMPTY LIST` and rewrote the empty predicates as `LENGTH OF` checks. Although Python lists are a valid implementation vehicle for this algorithm, that canonical source silently changed the supplied stack abstraction into list data.

## Change

GC124 now preserves the stack abstraction explicitly:

```text
Stack1 <- CALL create_stack()
Stack2 <- CALL create_stack()

FUNCTION ENQUEUE ACCEPTS(Item)
    CALL PUSH(Item, Stack1)
ENDFUNCTION

FUNCTION DEQUEUE ACCEPTS()
    IF CALL stack_is_empty(Stack2) THEN
        WHILE NOT CALL stack_is_empty(Stack1) DO
            CALL PUSH(CALL POP(Stack1), Stack2)
        ENDWHILE
    ENDIF

    OUTPUT CALL POP(Stack2)
ENDFUNCTION
```

The two compatibility intrinsics are ordinary AJ v1.2 `CALL` expressions; no grammar revision is required. The Python compiler lowers the explicit stack abstraction to a list-backed implementation:

```python
Stack1 = []
Stack2 = []
```

`PUSH` remains lowered to `.append(...)`, `POP` to `.pop(...)`, and `stack_is_empty(stack)` to a zero-length test. These are compiler implementation details rather than claims that the canonical pseudocode's stack variables are list values.

This release does **not** alter GC121. `CREATE Stack` in the array-backed Algorithm 37 remains unresolved because its required capacity/dimensions are absent from the source.

## Validation

- focused GC124 tests: 5 passed
- pytest: 917 passed, 3 skipped, 5 subtests passed
- unittest: 313 passed, 1 skipped
- historical AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
- active AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`
