# INTEGER DIVISION negative-operand semantics audit — v3.97 working tree

## Decision

AJ `INTEGER DIVISION` remains lowered to Python floor division (`//`). No compiler change is warranted.

## Current semantics

For positive operands this matches the corpus uses audited to date.

For negative, non-exact quotients Python floors toward negative infinity. For example:

```text
-3 INTEGER DIVISION 2
```

lowers to:

```python
-3 // 2  # -2
```

The corresponding Python `MODULUS` result follows the floor-division identity:

```python
-3 % 2  # 1
```

so `a == (a // b) * b + (a % b)` remains true.

## Alternative interpretation considered

A plausible alternative pseudocode convention is integer division truncated toward zero. Under that convention:

```text
-3 INTEGER DIVISION 2
```

would produce `-1`, and the paired remainder convention would typically produce `-1` rather than Python's `1` for `-3 MODULUS 2`.

## Expected consequences

The two interpretations agree for:

- non-negative operands;
- exact divisions;
- any audited corpus case that does not exercise a negative, non-exact quotient.

They diverge when the quotient is negative and fractional. The current compiler intentionally retains Python floor semantics unless the AJ dialect is later amended to define truncation toward zero explicitly.

## Audit classification

- current `INTEGER DIVISION -> //`: ACCEPTED
- current `MODULUS -> %`: ACCEPTED as the matching Python floor-division remainder convention
- truncation-toward-zero alternative: DOCUMENTED, not adopted
- compiler change: NO
- dialect change: NO
- package/version change: NO
