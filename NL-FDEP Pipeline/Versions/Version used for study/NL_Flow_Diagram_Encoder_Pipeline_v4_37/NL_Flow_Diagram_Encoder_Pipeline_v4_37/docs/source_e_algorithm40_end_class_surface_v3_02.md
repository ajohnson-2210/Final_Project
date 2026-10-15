# source_e Algorithm 40 — class terminator surface audit (v3.02)

## Motivating occurrence

source_e Algorithm 40 supplies an explicit queue class using two stack-backed collections and closes the class with the spaced legacy terminator:

```text
CLASS QUEUE
  stack1 = []
  stack2 = []
  ...
END CLASS
```

The queue operations themselves are complete. Existing recovery already handles the explicit stack/list backing, simple and nested `push(...)`, `pop()`, and frozen-AJ class canonicalisation.

## Source problem

`END CLASS` is a spelling variant of the frozen AJ terminator `ENDCLASS`. Before v3.02 it prevented the existing explicit-class recovery from recognising the otherwise complete class boundary.

## Approved recovery

`GC205` canonicalises a standalone, case-insensitive:

```text
END CLASS
```

to:

```text
ENDCLASS
```

No class body, constructor, state, method, stack, or queue semantics are supplied by GC205.

## Classification

**PASS AFTER CONSERVATIVE CLASS-TERMINATOR SURFACE NORMALISATION**

- semantic inference: **NO**
- algorithmic reconstruction: **NO**
- control-flow change: **NO**
- dialect change: **NO**
- existing stack/class recovery reused: **YES**
