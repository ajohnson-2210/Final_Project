# Function-shaped arithmetic surface recovery — v2.98

v2.98 generalises the existing arithmetic canonicalisation to accept equivalent raw and already-prefixed free-call surfaces.

Accepted modulus surfaces include:

```text
MOD(a, b)
MODULUS(a, b)
CALL MOD(a, b)
CALL MODULUS(a, b)
```

These canonicalise to:

```text
(a MODULUS b)
```

Accepted floor-of-division surfaces include:

```text
FLOOR(a / b)
CALL FLOOR(a / b)
```

These canonicalise to:

```text
(a INTEGER DIVISION b)
```

The implementation remains source-shape independent. It does not inspect model name, filename, algorithm number, routine name, or variable names.

## Safety boundaries

- Member methods such as `calculator.MOD(a, b)` and `calculator.FLOOR(a / b)` are not reclassified.
- Identifier names merely containing `MOD`, such as `MYMOD(a, b)`, are not reclassified.
- Unsupported arities such as `MOD(a, b, c)` are not partially rewritten.
- `FLOOR(a)` is not converted to integer division because no explicit division expression is supplied.
- The AJ v1.1 dialect is unchanged.
