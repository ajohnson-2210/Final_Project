# source_f Algorithm 27 — source-division expected-failure audit — v3.90

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

## Preserved arithmetic boundary

The source explicitly supplies ordinary division in the outer loop bound:

```text
N / 2 - 1
```

The square-matrix annotation justifies resolving the otherwise-unbound `N` references to `LENGTH OF matrix`; it does **not** justify changing arithmetic. Canonical AJ therefore preserves:

```text
LENGTH OF matrix / 2
```

and generated Python preserves:

```python
len(matrix) / 2
```

Python `range(...)` requires an integer bound, so executing the generated function raises `TypeError` when it reaches this loop.

The pipeline must not silently replace `/` with `DIV` / `//`. That would correct source-authored arithmetic and hide precisely the kind of source defect the study is intended to measure.

## Counterfactual viability audit

The surrounding rotation algorithm is otherwise viable. As an **audit-only counterfactual**, changing only the supplied arithmetic from ordinary division to integer division:

```text
N DIV 2
```

corresponding to:

```python
len(matrix) // 2
```

allows the unchanged surrounding algorithm to rotate representative square matrices correctly.

Observed counterfactual results:

```text
[[1, 2],
 [3, 4]]
```

becomes:

```text
[[3, 1],
 [4, 2]]
```

and:

```text
[[1, 2, 3],
 [4, 5, 6],
 [7, 8, 9]]
```

becomes:

```text
[[7, 4, 1],
 [8, 5, 2],
 [9, 6, 3]]
```

A 4x4 representative case is also audit-tested.

This counterfactual is evidence for diagnosis only. It is **not** applied by normalisation or compilation.

## Audit classification

source_f Algorithm 27: **EXPECTED EXECUTABLE-CORRECTNESS FAILURE — SOURCE INTEGER-DIVISION REQUIREMENT NOT SUPPLIED**.

- square-dimension identifier recovery: YES, source-proven
- `/` preserved as ordinary division: YES
- `/` -> `DIV` / `//` correction: NO
- source arithmetic repaired by compatibility rule: NO
- algorithm otherwise viable with only the arithmetic corrected: YES, audit-only counterfactual evidence
- trustworthy executable pass classification: NO
- dialect change: NO

The exact motivating source and both the observed failure and counterfactual viability checks are retained in `tests/test_source_f_algorithm27_square_dimension_division_v3_11.py`.
