# source_b Algorithm 37 canonical AJ class recovery — v2.83

## Purpose

This record documents the approved refinement of the v2.82 stateful-ADT recovery for source_b Algorithm 37. The empirical source occurrence remains the same: an outer zero-argument `FUNCTION Stack()` creates `data <- []` and contains nested `push`, `pop`, and `peek` operations that all act on that state.

v2.82 established that the literal outer-function interpretation is unusable: the generated Python function returns `None`, so the supplied `push`, `pop`, and `peek` interface cannot be discovered from the result. The study audit therefore approved stateful-ADT structural recovery.

v2.83 corrects the *canonical AJ representation* of that approved recovery. The frozen AJ_24038155 Dialect v1.0 specifies `PROPERTY`, `CONSTRUCTOR`, and `METHOD` constructs. The v2.82 implementation used an older internal compatibility representation (`CLASS ... ACCEPTS()`, top-level assignments, nested `FUNCTION`s). That representation generated the right Python behaviour but did not match the frozen class grammar.

## Source-preserving constructor decision

source_b explicitly initialises the state internally:

```text
FUNCTION Stack():
    data <- []
```

Therefore the constructor must remain zero-argument. A constructor such as `CONSTRUCTOR ACCEPTS(data)` would change the algorithm by moving responsibility for state initialisation to the caller. No such parameter is introduced.

Canonical recovery:

```text
CLASS Stack
    PROPERTY data AS LIST

    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.data <- EMPTY LIST
    ENDCONSTRUCTOR

    METHOD push ACCEPTS(item)
        APPEND item TO THIS.data
    ENDMETHOD

    METHOD pop ACCEPTS()
        IF LENGTH OF THIS.data == 0 THEN
            RETURN STRING("Underflow")
        ENDIF
        RETURN REMOVE LAST ITEM FROM THIS.data
    ENDMETHOD

    METHOD peek ACCEPTS()
        IF LENGTH OF THIS.data == 0 THEN
            RETURN STRING("Empty")
        ENDIF
        RETURN THIS.data[-1]
    ENDMETHOD
ENDCLASS
```

Expected Python behaviour:

```python
class Stack:
    def __init__(self):
        self.data = []

    def push(self, item):
        self.data.append(item)

    def pop(self):
        if len(self.data) == 0:
            return "Underflow"
        return self.data.pop(-1)

    def peek(self):
        if len(self.data) == 0:
            return "Empty"
        return self.data[-1]
```

## Parser/compiler measure

v2.83 adds native support for the already-documented AJ v1.0 class constructs:

- `PROPERTY name [AS type]`
- `PROPERTY THIS.name <- expression`
- `CONSTRUCTOR ACCEPTS(parameters) ... ENDCONSTRUCTOR`
- `METHOD name ACCEPTS(parameters) ... ENDMETHOD`
- contextual `THIS.property` compilation to Python `self.property`

The older internal `CLASS Name ACCEPTS(...)` representation remains accepted for backwards compatibility with earlier compatibility rules and historical tests.

## GC196 refinement

GC196 now emits the canonical class grammar when its existing stateful-ADT evidence safeguards succeed:

1. one top-level zero-argument outer function;
2. explicit persistent-state assignment(s) before nested operations;
3. at least two nested operations;
4. every nested operation uses the supplied persistent state;
5. no meaningful outer return, call, or control-flow statement;
6. no algorithm or method name is hard-coded.

For an obvious empty collection state, GC196 emits the corresponding property type (`LIST`, `DICTIONARY`, `SET`, `STRING`, or `TUPLE`). The source RHS remains the constructor initialiser. Nested operation references to the recovered state are qualified as `THIS.<property>`.

## Audit classification

```text
status:
    PASS AFTER STATEFUL-ADT STRUCTURAL RECOVERY

representation refinement:
    v2.83 uses the frozen AJ v1.0 PROPERTY / CONSTRUCTOR / METHOD grammar

constructor parameters invented:
    NO

constructor behaviour changed:
    NO

state initialisation:
    remains internal and empty, exactly as supplied by source

semantic inference:
    LIMITED STRUCTURAL INFERENCE (function-container -> class/ADT)

algorithmic reconstruction:
    NO

control flow changed:
    NO

interface invented:
    NO — push/pop/peek are explicit in source
```
