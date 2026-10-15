# RANGE integer-offset folding — v3.19

## Scope

The Python compiler may simplify only AJ RANGE end expressions. RANGE endpoints are integer-valued, and generic inclusive-source lowering can introduce literal additive offsets such as the synthetic `+ 1` used to preserve inclusive `TO` semantics.

## Approved fold

When the same left-associated additive chain contains at least two literal integer offsets, combine those offsets and preserve the relative order of every non-literal term.

Examples:

- `(Limit - 2) + 1` -> `Limit - 1`
- `(N - 1) + 1` -> `N`
- `(Index + 3) - 1` -> `Index + 2`
- `(Value - 4) - 2` -> `Value - 6`
- `(Value + 2) - 2` -> `Value`
- `((LENGTH OF xs - 2) - i) + 1` -> `len(xs) - 1 - i`

## Refusals

The compiler does not apply this fold to a single literal offset, floating-point offsets, multiplication/division, or additive algebra nested on the right side such as `A - (B - 2)`. The rule is not a general arithmetic optimiser and does not alter the canonical AJ AST or frozen dialect.
