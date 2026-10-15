# source_c Algorithm 28 — nested list-append canonicalisation — v2.92

## Motivating occurrence

```text
FUNCTION slidingWindowMax(arr, k):
    result = empty list
    deque = empty deque
    FOR i FROM 0 TO length(arr)-1:
        WHILE deque IS NOT empty AND deque.front() <= i - k:
            deque.pop_front()
        WHILE deque IS NOT empty AND arr[deque.back()] <= arr[i]:
            deque.pop_back()
        deque.push_back(i)
        IF i >= k - 1:
            result.append(arr[deque.front()])
    RETURN result
```

## Finding

The source is algorithmically complete. `result` is explicitly declared as a list and `result.append(...)` is already a valid Python list operation. The compatibility failure was therefore not a missing semantic operation: AJ_24038155 Dialect v1.1 has its own canonical list statement, `APPEND value TO list`, and the existing GC033 regex only recognised `.append(...)` when its argument contained no nested parentheses.

In the motivating line, the explicit append value contains `deque.front()`, so the line survived GC033. A later deque normaliser simplified `deque.front()` to `deque[0]`, but GC033 had already run and strict AJ parsing then encountered the reserved word `append` as a member name.

## v2.92 recovery

GC200 adds a balanced-parenthesis path for a standalone `name.append(expression)` only when `name` has explicit LIST evidence in the same source. For example:

```text
result <- EMPTY LIST
result.append(arr[deque.front()])
```

becomes:

```text
APPEND arr[deque.front()] TO result
```

and the existing deque surface rule subsequently gives:

```text
APPEND arr[deque[0]] TO result
```

The balanced path preserves nested calls, indexing and quoted parentheses in the argument. It does not infer an arbitrary receiver to be a list. A nested `.append(...)` on a receiver without explicit list evidence is left unchanged.

Simple `.append(value)` recovery continues to use the existing GC033 path for backwards compatibility.

## Canonical AJ

```text
FUNCTION slidingWindowMax ACCEPTS(arr, k)
    result <- EMPTY LIST
    deque <- EMPTY LIST
    FOR i <- IN RANGE 0 TO (LENGTH OF arr-1) + 1 DO
        WHILE LENGTH OF deque > 0 AND deque[0] <= i - k DO
            REMOVE FIRST ITEM FROM deque
        ENDWHILE
        WHILE LENGTH OF deque > 0 AND arr[deque[-1]] <= arr[i] DO
            REMOVE LAST ITEM FROM deque
        ENDWHILE
        APPEND i TO deque
        IF i >= k - 1 THEN
            APPEND arr[deque[0]] TO result
        ENDIF
    ENDFOR
    RETURN result
ENDFUNCTION
```

## Expected Python

```python
def slidingWindowMax(arr, k):
    result = []
    deque = []
    for i in range(0, len(arr)):
        while len(deque) > 0 and deque[0] <= i - k:
            deque.pop(0)
        while len(deque) > 0 and arr[deque[-1]] <= arr[i]:
            deque.pop()
        deque.append(i)
        if i >= k - 1:
            result.append(arr[deque[0]])
    return result
```

Behavioural regression:

```text
slidingWindowMax([1, 3, -1, -3, 5, 3, 6, 7], 3)
-> [3, 3, 5, 5, 6, 7]
```

## Classification

```text
status: PASS AFTER CANONICAL AJ LIST-SYNTAX NORMALISATION
semantic inference: NO
algorithmic reconstruction: NO
control-flow change: NO
dialect change: NO
```

The implementation contains no source_c, corpus filename, algorithm number, or `slidingWindowMax` condition. The exact occurrence is retained only as motivating audit evidence.
