# v3.95 — unresolved punctuation dependency enforcement

v3.95 completes the punctuation-predicate boundary established in v3.94.

A bare canonical call:

```text
CALL is_punctuation(value)
```

no longer reaches generated Python when the supplied AJ program does not define
that exact helper.  The compiler returns an expected-failure result with no
Python source emitted.  This prevents an undefined punctuation abstraction from
being mistaken for executable code merely because the call spelling is valid.

An explicitly supplied `FUNCTION is_punctuation ... ENDFUNCTION` remains
authoritative and compiles normally.  The accepted singular character predicates
`is_number`, `is_digit`, and `is_uppercase` remain unchanged.

## Compiler change

The unresolved-source-abstraction guard now includes `is_punctuation` alongside
the existing ordered-cache helper boundary.  Other ordinary external calls remain
permitted; this is a specific semantic-integrity guard for abstractions whose
meaning the compiler is not allowed to invent.

## Dialect impact

None. AJ dialect v1.2 is unchanged.

## Validation

983 pytest passed, 3 skipped, 5 subtests passed; 327 unittest passed, 1 skipped.
