# v4.04 — canonical RANDOM expression support

v4.04 adds first-class parser, flow-diagram, static-semantic, and Python-compiler support for the frozen AJ v1.2 RANDOM expression family:

```text
RANDOM INT(minimum, maximum)
RANDOM FLOAT(minimum, maximum)
RANDOM BOOLEAN()
```

## Parser and AST support

The three canonical forms are represented by `RandomExpressionNode` with a `random_type` discriminator and, for INT/FLOAT, explicit minimum and maximum expressions. Arity is fixed by the frozen grammar: INT/FLOAT require exactly two bounds and BOOLEAN requires zero arguments.

## Static semantics

Validation remains conservative and evidence-based:

- `RANDOM INT` rejects a bound only when that bound is statically known not to be INTEGER. Unknown bound types remain unresolved rather than inferred.
- `RANDOM FLOAT` accepts statically known INTEGER or FLOAT bounds and rejects statically known non-numeric bounds. Unknown bound types remain unresolved.
- `RANDOM BOOLEAN()` has result type BOOLEAN.
- `RANDOM INT(...)` has result type INTEGER.
- `RANDOM FLOAT(...)` has result type FLOAT.

These result types participate in the existing explicit-known-type rules, including Boolean-condition validation.

## Python compiler backing

AJ v1.2 explicitly specifies that both `RANDOM INT` endpoints are inclusive. v4.04 therefore lowers it to Python `random.randint(minimum, maximum)`.

The frozen dialect names `RANDOM FLOAT` and `RANDOM BOOLEAN` but does not define their probability distributions. v4.04 records the following deterministic compiler conventions rather than presenting them as dialect guarantees:

- `RANDOM FLOAT(a, b)` lowers to Python `random.uniform(a, b)`.
- `RANDOM BOOLEAN()` lowers to `bool(random.getrandbits(1))`, giving an unbiased 50/50 Boolean choice under Python's random generator.

The random module is imported through a fresh compiler-only alias (normally `_aj_random`) selected against all source-authored identifiers, preventing a source variable such as `random` or `_aj_random` from shadowing the backing module.

No seed is invented. Programs therefore retain Python's ordinary random-module seeding behaviour unless surrounding test/runtime code explicitly seeds it.

## Dialect impact

None. AJ dialect v1.1 and v1.2 source documents are unchanged.

- AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
- AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`

## Validation

1103 pytest passed, 3 skipped, 5 subtests passed; 332 unittest passed, 1 skipped.
