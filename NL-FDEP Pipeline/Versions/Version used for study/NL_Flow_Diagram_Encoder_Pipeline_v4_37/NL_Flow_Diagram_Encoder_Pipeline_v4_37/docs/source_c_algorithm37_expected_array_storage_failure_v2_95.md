# source_c Algorithm 37 expected-failure audit — v2.95

## Motivating study occurrence

```text
CLASS Stack:
    stackArray = empty array
    topIndex = -1

    FUNCTION push(item):
        topIndex = topIndex + 1
        stackArray[topIndex] = item

    FUNCTION pop():
        IF topIndex < 0:
            RETURN NULL // Stack underflow
        item = stackArray[topIndex]
        topIndex = topIndex - 1
        RETURN item

    FUNCTION peek():
        IF topIndex < 0:
            RETURN NULL
        RETURN stackArray[topIndex]
```

## Boundary decision

The source has a recoverable structural omission (`ENDCLASS`), but structural closure is not sufficient to produce faithful executable Python. The supplied storage starts as an empty abstract array and the first push writes directly to index zero. Under the pipeline's existing Python-list representation this raises `IndexError`.

Silently replacing the indexed write with unconditional `append` is not faithful: after a pop the source decrements `topIndex` without removing the old backing-array element, so a later push is an overwrite at an existing index rather than an append. A correct Python-list implementation would therefore require additional append-or-overwrite logic, preallocation semantics, or a changed pop operation. None of those routines/semantics is supplied by the source.

v2.95 consequently adds no production recovery for this case. It records and regression-locks the non-inference boundary instead.

## Classification

```text
Algorithm: source_c 37 — Stack Using Array
status: EXPECTED FAIL — INSUFFICIENT ARRAY GROWTH / STORAGE SEMANTICS
secondary structural omission: missing ENDCLASS
structural recovery alone sufficient: NO
semantic inference required for executable Python: YES
algorithmic/storage reconstruction required: YES
invent append-or-overwrite logic: NO
invent preallocation/capacity: NO
change pop to remove backing storage: NO
dialect change: NO
```

AJ_24038155 Dialect v1.1 remains frozen and unchanged.
