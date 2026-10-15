# source_e Algorithm 2 audit — v2.98

## Motivating occurrence

```text
FUNCTION DECIMAL_TO_BINARY(n)
  IF n == 0 THEN
    RETURN "0"
  END IF
  binary = ""
  WHILE n > 0
    binary = MOD(n, 2) + binary
    n = FLOOR(n / 2)
  END WHILE
  RETURN binary
END FUNCTION
```

The source explicitly supplies the decimal-to-binary algorithm. The only new mismatch is the raw function-shaped arithmetic surface `MOD(n, 2)` / `FLOOR(n / 2)`.

## Classification

- status: **PASS AFTER CONSERVATIVE FUNCTION-SHAPED ARITHMETIC RECOVERY**
- semantic inference: **NO NEW SEMANTIC INFERENCE**
- algorithmic reconstruction: **NO**
- source logic correction: **NO**
- dialect change: **NO**

## Canonical AJ

```text
FUNCTION DECIMAL_TO_BINARY ACCEPTS(n)
  IF n == 0 THEN
    RETURN STRING("0")
  ENDIF
  binary <- EMPTY STRING
  WHILE n > 0 DO
    binary <- CALL to_string((n MODULUS 2)) + binary
    n <- (n INTEGER DIVISION 2)
  ENDWHILE
  RETURN binary
ENDFUNCTION
```

The explicit string coercion is pre-existing pipeline behaviour for prepending a numeric modulus result to an evidenced string; v2.98 does not introduce that semantic rule.

## Expected Python

```python
def DECIMAL_TO_BINARY(n):
    if n == 0:
        return "0"
    binary = ""
    while n > 0:
        binary = str(n % 2) + binary
        n = n // 2
    return binary
```

`DECIMAL_TO_BINARY(10)` returns `"1010"`.
