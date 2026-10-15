# source_e Algorithm 43 — function-shaped output audit (v3.03)

## Motivating occurrence

source_e Algorithm 43 supplies a complete recursive Tower of Hanoi implementation and renders move messages with function-shaped output:

```text
FUNCTION TOWER_OF_HANOI(N)
  FUNCTION MOVE(n, from_rod, to_rod, aux_rod)
    IF n == 1 THEN
      PRINT("Move disk 1 from rod " + from_rod + " to rod " + to_rod)
    ELSE
      MOVE(n - 1, from_rod, aux_rod, to_rod)
      PRINT("Move disk " + n + " from rod " + from_rod + " to rod " + to_rod)
      MOVE(n - 1, aux_rod, to_rod, from_rod)
    END IF
  END FUNCTION
  MOVE(N, "A", "C", "B")
END FUNCTION
```

## Source problem

`PRINT(expression)` is an explicit output operation, but frozen AJ v1.1 uses statement-shaped `OUTPUT expression`. Before v3.03 the generic free-call recovery treated `PRINT(...)` as `CALL PRINT(...)`, producing an unsupported routine call.

The mixed text/value expression does not require an AJ typecast. The existing Python compiler already has a narrow `OUTPUT` rendering rule that turns a literal/identifier `+` message chain into an f-string.

## Approved recovery

GC206 canonicalises a standalone, balanced, single-expression:

```text
PRINT(expression)
```

to:

```text
OUTPUT expression
```

No `CALL to_string(...)` or `str(...)` cast is inserted. The canonical AJ keeps the source values unchanged, for example:

```text
OUTPUT STRING("Move disk ") + n + STRING(" from rod ") + from_rod + STRING(" to rod ") + to_rod
```

The existing compiler then renders that `OUTPUT` message as:

```python
print(f"Move disk {n} from rod {from_rod} to rod {to_rod}")
```

## Classification

**PASS AFTER CONSERVATIVE FUNCTION-SHAPED OUTPUT RECOVERY AND OUTPUT-FORMATTING LOWERING**

- source algorithm: **COMPLETE**
- semantic inference: **NO**
- algorithmic reconstruction: **NO**
- control-flow reconstruction: **NO**
- explicit typecast inserted: **NO**
- source logic correction: **NO**
- dialect change: **NO**
