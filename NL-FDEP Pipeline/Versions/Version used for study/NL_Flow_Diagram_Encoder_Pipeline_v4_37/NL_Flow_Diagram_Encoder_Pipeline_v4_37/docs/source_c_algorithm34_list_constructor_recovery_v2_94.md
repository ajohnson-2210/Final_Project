# source_c Algorithm 34 audit — v2.94

## Source occurrence

```text
FUNCTION commonElements(list1, list2):
    set1 = set(list1)
    result = empty set
    FOR each item in list2:
        IF item IN set1:
            result.add(item)
    RETURN list(result)
```

## v2.93 failure

The set construction and set insertion already had explicit canonical AJ representations, but `RETURN list(result)` retained the Python-like `list(...)` surface. Because `LIST` is an AJ keyword, strict parsing could not treat it as a free function name.

The operation is nevertheless explicit in the source: Python's built-in `list(result)` constructor is requested directly. No semantic inference is needed.

## v2.94 canonical AJ

```text
FUNCTION commonElements ACCEPTS(list1, list2)
    set1 <- CALL to_set(list1)
    result <- EMPTY SET
    FOR EACH item IN list2 DO
        IF item IN set1 THEN
            CALL add_to_set(result, item)
        ENDIF
    ENDFOR
    RETURN CALL to_list(result)
ENDFUNCTION
```

## Generated Python

```python
def commonElements(list1, list2):
    set1 = set(list1)
    result = set()
    for item in list2:
        if item in set1:
            result.add(item)
    return list(result)
```

A behavioural regression confirms that `[1, 2, 2, 3]` and `[2, 3, 4, 3]` produce the common-value set `{2, 3}` after converting the returned list for order-independent comparison.

## Classification

```text
status: PASS AFTER CANONICAL AJ LIST-CONSTRUCTOR SURFACE NORMALISATION
semantic inference: NO
algorithmic reconstruction: NO
control-flow change: NO
source operation: explicit Python list(...) constructor
canonical AJ: CALL to_list(...)
dialect change: NO
```

The motivating occurrence is empirical audit evidence only. GC201 contains no source_c, corpus-file, algorithm-number or function-name condition.
