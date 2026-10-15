# source_f Algorithm 13 audit evidence — v3.08

## Source occurrence

```text
INPUT s

chars = array(s)
left = 0
right = length(s)-1

WHILE left < right:
    swap(chars[left], chars[right])
    left++
    right--

RETURN join(chars)
```

The reversing algorithm is complete. The two approved compatibility questions are representational: the free one-argument `array(s)` conversion and the free one-argument `join(chars)` rendering operation.

## Approved recovery

```text
array(value)
```

is represented using the existing AJ/Python list conversion:

```text
CALL to_list(value)
```

and:

```text
join(collection)
```

is represented with its approved conventional empty separator:

```text
JOIN(collection, EMPTY STRING)
```

For the motivating occurrence, canonical AJ therefore contains:

```text
chars <- CALL to_list(s)
...
RETURN JOIN(chars, EMPTY STRING)
```

and expected Python contains:

```python
chars = list(s)
...
return ''.join(chars)
```

## Boundary

- `array(value)` recovery is free-call and exactly one balanced top-level argument only;
- member `.array(...)`, zero-argument and multi-argument calls are not reinterpreted;
- `join(collection)` recovery is free-call and exactly one balanced top-level argument only;
- native/two-argument `JOIN(collection, separator)` remains native and unchanged;
- member `.join(...)`, zero-argument and multi-argument calls are not defaulted;
- quoted strings and comments are not rewritten;
- no helper implementation or import is invented.

- semantic inference: **LIMITED REPRESENTATION INFERENCE**
- algorithmic reconstruction: **NO**
- source control-flow correction: **NO**
- dialect change: **NO**
