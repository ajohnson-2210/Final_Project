# source_f Algorithm 27 — square-dimension recovery and integer-division expected-failure audit — v3.11

## Motivating occurrence

```text
INPUT matrix (N x N)

FOR i from 0 to N/2 - 1:
    FOR j from i to N-1-i-1:
        temp = matrix[i][j]
        matrix[i][j] = matrix[N-1-j][i]
        matrix[N-1-j][i] = matrix[N-1-i][N-1-j]
        matrix[N-1-i][N-1-j] = matrix[j][N-1-i]
        matrix[j][N-1-i] = temp

RETURN matrix
```

## Approved representation recovery

The source explicitly annotates `matrix` as `N x N`. GC212 therefore resolves otherwise-unbound executable references to `N` directly as `LENGTH OF matrix` in the same unnamed routine.

Examples:

```text
N-1-j
```

becomes:

```text
LENGTH OF matrix-1-j
```

and:

```text
N/2 - 1
```

becomes:

```text
LENGTH OF matrix/2 - 1
```

No synthetic assignment such as:

```text
N <- LENGTH OF matrix
```

is introduced.

## Integer-division boundary

The source explicitly uses ordinary `/` in the outer layer bound. Frozen AJ v1.1 distinguishes `/` from `INTEGER DIVISION`, and compatibility normalisation must not change arithmetic operators to repair source logic.

Accordingly, generated Python retains ordinary division and contains an equivalent of:

```python
for i in range(0, len(matrix) / 2):
```

Python rejects the float range endpoint with `TypeError`. The pipeline must expose this source requirement rather than silently converting `/` to `//`.

## Audit classification

source_f 27: **EXPECTED EXECUTABLE-CORRECTNESS FAILURE — SOURCE INTEGER-DIVISION REQUIREMENT NOT SUPPLIED**.

- square-dimension reference recovery: **YES**, through GC212
- `N` semantic inference from algorithm convention: **NO**
- `N` representation from explicit `(N x N)` annotation: **YES**
- synthetic `N` variable: **NO**
- `/` -> `INTEGER DIVISION`: **NO**
- algorithmic source correction: **NO**
- complete trustworthy Python: **NO**
- dialect change: **NO**

The exact occurrence is retained in `tests/test_source_f_algorithm27_square_dimension_division_v3_11.py` and generic GC212 boundaries are covered separately in `tests/test_square_dimension_identifier_reference_recovery_v3_11.py`.
