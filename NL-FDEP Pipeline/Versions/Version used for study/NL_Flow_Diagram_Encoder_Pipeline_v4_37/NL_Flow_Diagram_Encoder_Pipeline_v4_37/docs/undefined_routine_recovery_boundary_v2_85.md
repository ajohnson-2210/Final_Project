# Undefined routine recovery boundary — v2.85

## Purpose

v2.85 formalises the semantic-integrity boundary used when generated pseudocode names or describes an operation whose executable behaviour is absent from the response.

A compatibility conversion may preserve or canonicalise a routine without reconstructing its internals only when at least one of the following is true:

1. the operation is a defined AJ intrinsic or has a deterministic compiler/runtime mapping;
2. the operation is a defined Python built-in/standard operation used by the compiler mapping;
3. the pseudocode explicitly defines the routine elsewhere in the same response; or
4. the pseudocode explicitly imports the external routine/library on which it relies.

A routine is **not** recoverable merely because its intended domain behaviour is familiar. Natural-language instructions such as `CHECK ...`, `RECORD solution`, `score and rank`, or `return the best ...` do not authorise the compatibility layer to invent loops, state, branches, return propagation, storage policy, failure sentinels, or helper implementations.

## Audit consequence

Where an essential non-built-in routine is undefined and unimported, the case remains an expected failure. Structural normalisation may preserve explicit syntax around that routine, but complete executable Python must not be fabricated.

## Regression requirement

Future parser/normaliser changes must not convert an expected failure into a pass by silently creating an implementation for an undefined routine. A pass is justified only if later source evidence supplies the missing routine/import or the operation becomes a formally defined dialect/runtime intrinsic.
