# source_e Algorithm 33 — error-string recovery and integer-division expected-failure audit — v3.01

## Motivating occurrence

```text
FUNCTION SQUARE_ROOT(n)
  IF n < 0 THEN
    RETURN ERROR
  END IF
  IF n == 0 OR n == 1 THEN
    RETURN n
  END IF
  low = 0
  high = n
  WHILE low <= high
    mid = (low + high) / 2
    IF mid * mid <= n THEN
      low = mid + 1
    ELSE
      high = mid - 1
    END IF
  END WHILE
  RETURN high
END FUNCTION
```

## Approved recovery

The explicit bare error result is represented canonically as:

```text
RETURN STRING("ERROR")
```

and therefore lowers to Python `return "ERROR"`.

This is not an exception. `RETURN` remains `RETURN`.

## Integer-division boundary

The source explicitly supplies:

```text
mid = (low + high) / 2
```

Canonical AJ therefore preserves:

```text
mid <- (low + high) / 2
```

and Python preserves ordinary `/` division.

The pipeline must **not** rewrite this to `INTEGER DIVISION` / `//` merely because a conventional binary-search integer-square-root implementation normally requires an integer midpoint. Such a rewrite would correct the supplied algorithm from inferred intent.

The retained source arithmetic is observably incorrect for the stated task. For example, the literal generated behaviour gives `2.5` for inputs such as `4` and `10`, rather than the expected floor square roots `2` and `3`.

## Audit classification

source_e 33: **EXPECTED EXECUTABLE-CORRECTNESS FAILURE — SOURCE INTEGER-DIVISION REQUIREMENT NOT SUPPLIED**.

- `RETURN ERROR` representation recovery: YES, as `RETURN STRING("ERROR")`
- `/` -> integer-division correction: NO
- semantic inference for midpoint: NO
- algorithmic reconstruction: NO
- source-logic correction: NO
- trustworthy pass classification: NO
- dialect change: NO

The exact motivating source is retained in `tests/test_source_e_algorithm33_error_string_and_division_audit_v3_01.py`. Generic, source-independent coverage for `GC204` is retained separately in `tests/test_return_error_string_representation_v3_01.py`.
