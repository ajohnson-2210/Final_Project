# source_f Algorithm 37 — counted-list stateful ADT recovery — v3.16

## Source occurrence

```text
INIT stack = []
size = 0

FUNCTION push(x):
    stack.append(x)
    size++

FUNCTION pop():
    IF size > 0:
        size--
        RETURN stack.pop()
    ELSE:
        ERROR

FUNCTION peek():
    IF size > 0:
        RETURN stack[size-1]
    ELSE:
        ERROR
```

## Evidence decision

The task requests a stack implemented using an array with `push`, `pop`, and `peek`. The response explicitly initialises one list-backed state value and one zero count before supplying those three operations. Every operation reads or mutates both persistent values. The source therefore provides direct structural evidence for a stateful ADT; wrapping that supplied state and interface in a neutral class does not invent an algorithm.

This differs from a generic collection/module recovery. The list and count are linked by explicit stack-shaped evidence: appending increments the count, popping decrements it, and peeking indexes `count - 1`.

## GC216 recovery

After ordinary generic normalisation, the relevant source shape becomes:

```text
stack <- EMPTY LIST
size <- 0

FUNCTION push ACCEPTS(x)
    APPEND x TO stack
    size <- size + 1
ENDFUNCTION
...
```

GC216 requires the complete counted-list evidence described in the release record. When proven, it emits:

```text
CLASS unnamed_class
    PROPERTY stack AS LIST
    PROPERTY size AS INTEGER

    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.stack <- EMPTY LIST
        PROPERTY THIS.size <- 0
    ENDCONSTRUCTOR

    METHOD push ACCEPTS(x)
        APPEND x TO THIS.stack
        THIS.size <- THIS.size + 1
    ENDMETHOD
    ...
ENDCLASS
```

The class name is intentionally neutral. The constructor has no invented parameter because the source already supplies both initial values.

## Standalone ERROR

source_f uses an exact `ERROR` statement in the empty-stack branches. GC217 maps only that statement-position spelling to:

```text
RAISE STRING("ERROR")
```

This does not change the existing GC204 rule for `RETURN ERROR`, which remains a string sentinel rather than an exception.

## Behavioural verification

The exact recovered source compiles to a Python class whose `push`, `pop`, and `peek` operations preserve the invariant:

```text
size == LENGTH OF stack
```

Deterministic randomized regression testing compares the recovered implementation with a reference Python list stack across mixed push/pop/peek operations, including underflow. Return values, state, count and error behaviour match.

## Classification

**PASS AFTER EVIDENCED STATEFUL-ADT STRUCTURAL RECOVERY — TRUSTWORTHY EXECUTABLE**

AJ_24038155 Dialect v1.1 remains frozen and unchanged.
