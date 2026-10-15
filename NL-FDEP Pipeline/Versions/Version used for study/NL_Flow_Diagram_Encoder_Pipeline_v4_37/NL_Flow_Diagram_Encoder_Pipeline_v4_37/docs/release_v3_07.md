# NL-FDEP v3.07 release record

## Scope

v3.07 implements the approved square-dimension reference resolution motivated by source_f Algorithm 12.

## Production change

GC208 recognises a uniquely evidenced square-shape annotation:

```text
INPUT collection (D x D)
```

and, when the same unbound annotation symbol appears in the exact zero-based inclusive source loop:

```text
FOR i from 0 to D-1:
```

canonicalises that loop directly as:

```text
FOR i <- IN RANGE 0 TO LENGTH OF collection DO
```

No runtime `D` variable is invented. Rectangular shapes, independently bound symbols, ambiguous annotations, other loop bounds, and other uses of `D` remain outside the rule.

## source_f Algorithm 12

The exact corpus occurrence now compiles to:

```python
for i in range(0, len(matrix)):
```

with no `N = len(matrix)` assignment.

## Audit boundary

- semantic inference: **DIRECTLY EVIDENCED REPRESENTATION ONLY**
- algorithmic reconstruction: **NO**
- source logic correction: **NO**
- synthetic dimension variable: **NO**
- rectangular-shape generalisation: **NO**
- dialect change: **NO**

## Dialect

AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## Validation

Working tree:

- pytest: **521 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**

Fresh extraction from packaged ZIP:

- pytest: **521 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
