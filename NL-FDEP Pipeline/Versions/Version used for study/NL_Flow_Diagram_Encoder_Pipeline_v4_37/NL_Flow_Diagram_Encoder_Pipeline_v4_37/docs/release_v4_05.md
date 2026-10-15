# v4.05 — safe AJ OUTPUT placeholders and accumulated static-semantic checks

v4.05 fixes the compiler boundary for AJ v1.2 string placeholders and packages the validated static-semantic improvements accumulated after v4.04.

## Safe OUTPUT placeholder semantics

AJ v1.2 defines string placeholders using the exact form `{identifier}` and requires the referenced identifier to exist in the current scope. v4.04 compiled any OUTPUT string containing braces as a raw Python f-string, which could accidentally evaluate arbitrary Python expression text such as `{1+2}`.

v4.05 changes that boundary:

- only exact `{identifier}` forms are treated as AJ placeholders;
- each placeholder identifier must be definitely bound at the OUTPUT point;
- all other brace content is preserved as literal text rather than evaluated;
- Python conversion happens only after the AJ placeholder scan, with non-placeholder braces escaped before a generated f-string is emitted;
- non-OUTPUT STRING values remain ordinary string data and are not implicitly interpolated.

Examples:

```text
OUTPUT STRING("Value: {value}")
```

still substitutes `value`, while:

```text
OUTPUT STRING("Value: {1+2}")
```

prints the literal text `Value: {1+2}`.

Likewise `{value!r}`, `{value:>4}`, and doubled braces such as `{{value}}` remain literal because AJ v1.2 does not define Python format-specifier, conversion, or brace-escape syntax.

## Member-method arity validation

The static validator now checks method argument counts only when receiver-class evidence is explicit:

- `THIS.method(...)` against the current AJ class;
- an explicitly class-typed parameter/identifier;
- a chain of explicitly typed class properties.

Unknown/external receiver protocols remain unchecked rather than inferred.

## Declared-type value-entry validation

The validator now rejects provably incompatible values entering explicitly typed locations:

- reassignment to typed parameters;
- `PROPERTY THIS.x <- value` for typed properties;
- arguments to resolved typed free functions;
- arguments to resolved typed methods.

Unknown expression types remain unknown. INTEGER/FLOAT retain the existing numeric compatibility rule.

## Dialect impact

None. AJ dialect v1.1 and v1.2 source documents are unchanged.

- AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
- AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`

## Validation

1129 pytest passed, 3 skipped, 5 subtests passed; 332 unittest passed, 1 skipped.
