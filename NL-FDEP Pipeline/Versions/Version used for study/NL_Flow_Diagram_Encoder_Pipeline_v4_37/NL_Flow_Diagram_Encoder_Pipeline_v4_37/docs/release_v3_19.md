# NL-FDEP v3.19 release record

## Summary

v3.19 implements the approved RANGE-end integer additive constant-folding policy. It supersedes the v3.18 exact `(X - 1) + 1 -> X` rendering special case with a guarded fold for two or more literal integer offsets on one left-associated `+`/`-` chain.

## Behaviour

Examples now emitted cleanly include:

- `(Limit - 2) + 1` -> `Limit - 1`
- `(Index + 3) - 1` -> `Index + 2`
- `(Value - 4) - 2` -> `Value - 6`
- `(Value + 2) - 2` -> `Value`
- `((LENGTH OF xs - 2) - i) + 1` -> `len(xs) - 1 - i`

The fold remains confined to Python RANGE end-expression rendering. It refuses single literal offsets, floats, multiplication/division, and nested right-hand additive algebra.

## Validation

- pytest: 639 passed, 3 skipped, 5 subtests passed
- unittest: 260 passed, 1 skipped
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`

AJ_24038155 Dialect v1.1 is unchanged.
