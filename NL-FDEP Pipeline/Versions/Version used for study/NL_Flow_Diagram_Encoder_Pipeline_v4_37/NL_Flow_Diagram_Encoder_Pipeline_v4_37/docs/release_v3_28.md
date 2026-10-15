# NL-FDEP v3.28 release record

## Scope

v3.28 implements the approved source_b Algorithm 2 compatibility fix while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC230 — direct modulus-digit string-accumulator recovery

GC230 handles the exact source-evidenced representation case where:

- a destination is independently proven string-backed by `EMPTY STRING` initialisation;
- the source directly assigns that same destination from a parenthesised `MOD` or `MODULUS` result prepended to the same accumulator; and
- no broader numeric/string coercion is required or inferred.

For example:

```text
result <- EMPTY STRING
result <- (n MOD 2) + result
```

is represented canonically as:

```text
result <- EMPTY STRING
result <- CALL to_string((n MODULUS 2)) + result
```

The generated Python therefore uses `str(n % 2) + result`.

The fix exists because this guarded direct-expression recovery runs before the later generic infix `MOD -> MODULUS` spelling canonicalisation. v3.27 recognised only the already-canonical `MODULUS` spelling at that earlier stage, so source `MOD` reached Python as integer-plus-string despite the source's explicit string accumulator.

GC230 refuses non-string destinations, a different right-hand accumulator, non-modulus arithmetic, and unrelated mixed-type additions. It does not alter decimal-to-binary control flow or arithmetic.

## source_b Algorithm 2

The supplied non-negative decimal-to-binary algorithm now parses, compiles, and returns the same binary strings as Python's reference representation across the regression range, including zero.

## Validation

The release is accepted only after the targeted GC230 tests, the full pytest suite, the unittest suite, a fresh-extraction rerun, and the frozen-dialect hash check pass.
