# source_f Algorithm 28 — evidenced camelCase deque recovery and source expected-failure audit — v3.12

## Source occurrence

```text
INPUT arr, k

result = []
deque = []

FOR i from 0 to length(arr)-1:
    IF deque[0] == i - k:
        deque.popFront()

    WHILE deque not empty AND arr[deque.back()] <= arr[i]:
        deque.popBack()

    deque.pushBack(i)

    IF i >= k - 1:
        result.append(arr[deque.front()])

RETURN result
```

## Representation decision

`deque = []` independently establishes that `deque` is list-backed. Therefore the camelCase deque operation spellings can be recovered mechanically without inferring algorithmic intent:

```text
deque.popFront() -> REMOVE FIRST ITEM FROM deque
deque.popBack()  -> REMOVE LAST ITEM FROM deque
deque.pushBack(i) -> APPEND i TO deque
```

This is GC213. It is receiver-evidence guarded and is not a global spelling rewrite.

The already-supported `front()` / `back()` access recovery and nested list `append(...)` recovery remain separate rules.

## Source defect kept visible

The source indexes `deque[0]` before the first insertion. Because `deque` is initially empty, faithful execution raises an `IndexError` on the first iteration for any non-empty `arr`.

The pipeline does not insert an empty-state guard. Such a change would add a missing condition and constitute algorithmic repair rather than representation recovery.

Expected classification:

**EXPECTED EXECUTABLE-CORRECTNESS FAILURE — SOURCE EMPTY-DEQUE GUARD NOT SUPPLIED**.

## Control

A regression-only control supplies the missing condition explicitly:

```text
IF deque not empty AND deque[0] == i - k:
```

With that source change, the same GC213 representation recovery compiles and returns the expected sliding-window maxima. This demonstrates that the camelCase compatibility gap is fixed independently of the source-level defect.

## Tests

Exact and boundary coverage is retained in:

`tests/test_source_f_algorithm28_camelcase_deque_v3_12.py`

The tests verify:

- three GC213 transformations occur on the exact source_f source;
- the missing guard is not introduced;
- the exact source still raises `IndexError`;
- explicitly guarded source executes correctly;
- identical method names on an unevidenced receiver are not rewritten;
- a nested `pushBack(CALL ...)` argument is preserved by balanced scanning.
