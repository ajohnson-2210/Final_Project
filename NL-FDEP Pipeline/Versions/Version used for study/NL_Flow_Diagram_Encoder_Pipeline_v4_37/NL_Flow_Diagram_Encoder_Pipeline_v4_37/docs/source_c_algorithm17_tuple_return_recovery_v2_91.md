# source_c Algorithm 17 — parenthesised tuple-return recovery — v2.91

## Motivating occurrence

```text
FUNCTION sumAndAverage(list):
    sum = 0
    FOR each num in list:
        sum = sum + num
    average = sum / length(list)
    RETURN (sum, average)
```

## Finding

The source algorithm is executable and complete. The failure was representational: the generic compatibility pass previously allowed `RETURN (sum, average)` to reach GC083, where `RETURN` could be misread as a free routine name and become `CALL RETURN (sum, average)`. A later legacy rule could repair some already-mangled shapes, but that made behaviour depend on pipeline ordering.

## v2.91 recovery

The corpus-wide statement rule now recognises parenthesised multi-value statement surfaces before generic free-call prefixing:

```text
RETURN (a, b)  -> RETURN TUPLE(a, b)
OUTPUT (a, b)  -> OUTPUT TUPLE(a, b)
```

`RETURN` is also explicitly protected as an AJ statement keyword in GC083. `OUTPUT` was already protected and remains so.

A single grouped expression is not reclassified:

```text
RETURN (a + b)
```

remains a single return expression.

Nested commas are depth-aware, so:

```text
RETURN (combine(a, b), transform(c))
```

becomes:

```text
RETURN TUPLE(CALL combine(a, b), CALL transform(c))
```

without splitting the arguments of `combine`.

## Canonical AJ

```text
FUNCTION sumAndAverage ACCEPTS(__reserved_keyword__List)
    sum <- 0
    FOR EACH num IN __reserved_keyword__List DO
        sum <- sum + num
    ENDFOR
    average <- sum / LENGTH OF __reserved_keyword__List
    RETURN TUPLE(sum, average)
ENDFUNCTION
```

## Expected Python

```python
def sumAndAverage(__reserved_keyword__List):
    sum = 0
    for num in __reserved_keyword__List:
        sum = sum + num
    average = sum / len(__reserved_keyword__List)
    return (sum, average)
```

Behavioural regression: `sumAndAverage([2, 4, 6]) == (12, 4.0)`.

## Classification

```text
status: PASS AFTER CONSERVATIVE TUPLE-RETURN RECOVERY
semantic inference: NO
algorithmic reconstruction: NO
control-flow change: NO
dialect change: NO
```

The implementation contains no source_c, corpus filename, algorithm number, or `sumAndAverage` condition. The exact occurrence is retained only as motivating audit evidence.
