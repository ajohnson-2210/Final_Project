# source_c Algorithm 40 audit — v2.96

## Source occurrence

```text
CLASS QueueUsingStacks:
    stack1 = empty stack (for enqueue)
    stack2 = empty stack (for dequeue)

    FUNCTION enqueue(item):
        stack1.push(item)

    FUNCTION dequeue():
        IF stack2 IS empty:
            WHILE stack1 IS NOT empty:
                stack2.push(stack1.pop())
        IF stack2 IS empty:
            RETURN NULL // Queue is empty
        RETURN stack2.pop()
```

## v2.95 failure

The queue algorithm is complete. The source explicitly supplies two stack-backed collections, enqueue by push, transfer by pop/push, empty checks and dequeue by pop.

The remaining incompatibilities were representational:

1. GC037 could canonicalise only simple `stack.push(value)` arguments, so the nested `stack2.push(stack1.pop())` survived.
2. The explicit legacy `CLASS` surface used class-level state assignments and `FUNCTION` methods rather than frozen AJ v1.1 `PROPERTY` / `CONSTRUCTOR` / `METHOD` syntax, and omitted the final class terminator.

No queue operation, branch or data-structure routine needed to be invented.

## v2.96 canonical AJ

```text
CLASS QueueUsingStacks
    PROPERTY stack1 AS LIST
    PROPERTY stack2 AS LIST

    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.stack1 <- EMPTY LIST
        PROPERTY THIS.stack2 <- EMPTY LIST
    ENDCONSTRUCTOR

    METHOD enqueue ACCEPTS(item)
        APPEND item TO THIS.stack1
    ENDMETHOD

    METHOD dequeue ACCEPTS()
        IF LENGTH OF THIS.stack2 == 0 THEN
            WHILE LENGTH OF THIS.stack1 > 0 DO
                APPEND THIS.stack1.pop() TO THIS.stack2
            ENDWHILE
        ENDIF
        IF LENGTH OF THIS.stack2 == 0 THEN
            RETURN CALL NULL()
        ENDIF
        RETURN THIS.stack2.pop()
    ENDMETHOD
ENDCLASS
```

## Generated Python

```python
class QueueUsingStacks:
    def __init__(self):
        self.stack1 = []
        self.stack2 = []

    def enqueue(self, item):
        self.stack1.append(item)

    def dequeue(self):
        if len(self.stack2) == 0:
            while len(self.stack1) > 0:
                self.stack2.append(self.stack1.pop())
        if len(self.stack2) == 0:
            return None
        return self.stack2.pop()
```

Behavioural evidence covers enqueueing A/B/C, dequeuing A/B, enqueueing D, then dequeuing C/D and finally `None`.

## Classification

```text
status: PASS AFTER CANONICAL AJ STACK-PUSH SURFACE NORMALISATION
        AND EXPLICIT STATEFUL CLASS CANONICALISATION
source algorithm: COMPLETE
semantic inference: NO new queue semantics
algorithmic reconstruction: NO
invented data-structure operation: NO
source push/pop operations: RETAINED
dialect change: NO
```

GC202 and GC203 are corpus-wide. Neither rule inspects source_c, a corpus filename, an algorithm number or `QueueUsingStacks`.

The v2.95 source_c 37 boundary remains intact: GC203 refuses to canonicalise an empty-list-backed class state that is directly targeted by an indexed write, so class repair cannot accidentally operationalise missing array-growth semantics.
