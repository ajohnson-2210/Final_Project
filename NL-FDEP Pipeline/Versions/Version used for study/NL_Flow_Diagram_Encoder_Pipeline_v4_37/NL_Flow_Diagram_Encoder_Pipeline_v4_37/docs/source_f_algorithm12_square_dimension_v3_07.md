# source_f Algorithm 12 audit evidence — v3.07

## Source occurrence

```text
INPUT matrix (N x N)

sum = 0

FOR i from 0 to N-1:
    sum += matrix[i][i]

RETURN sum
```

The source explicitly annotates `matrix` as an `N x N` square matrix and uses `N` only as the inclusive upper-bound symbol in the diagonal loop.

## Approved recovery

The annotated square dimension is represented directly in the canonical loop bound rather than materialising a synthetic runtime variable:

```text
FOR i <- IN RANGE 0 TO LENGTH OF matrix DO
```

Expected Python lowering is therefore:

```python
for i in range(0, len(matrix)):
```

No `N <- LENGTH OF matrix` / `N = len(matrix)` binding is introduced.

## Boundary

- the annotation must be a single-symbol square shape `D x D`;
- the source loop must be exactly the zero-based inclusive form `0 to D-1`;
- the symbol must not be independently supplied, assigned, or bound as a loop variable;
- one dimension symbol must identify one unique annotated collection;
- rectangular `R x C` shapes are not generalised;
- other occurrences of the annotation symbol are not substituted.

- semantic inference: **DIRECTLY EVIDENCED REPRESENTATION ONLY**
- algorithmic reconstruction: **NO**
- source logic correction: **NO**
- synthetic dimension variable: **NO**
- dialect change: **NO**
