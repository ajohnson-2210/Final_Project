# v3.97 — unresolved N-Queens core abstraction guard

v3.97 extends the compiler's existing unresolved-source-abstraction boundary to
source_f-style N-Queens helpers whose semantics are not supplied by the source.

## Compiler change

Calls to the following source abstractions now require an explicit AJ function
definition before Python generation:

- `isSafe(...)`
- `emptyBoard(...)`

If either helper is called but not defined, compilation returns an expected
failure with no Python source emitted. This prevents the compiler from treating
missing core algorithm/representation semantics as executable external library
calls.

This is intentionally narrow. Unrelated external calls remain permitted, and
explicit source definitions of `isSafe` or `emptyBoard` remain authoritative.

## Semantic rationale

`isSafe` contains the essential N-Queens column/diagonal conflict policy, while
`emptyBoard` determines the board representation and initial contents. Neither
meaning can be reconstructed without adding semantics that are absent from the
source pseudocode.

## Dialect impact

None. AJ dialect v1.1 and v1.2 source documents are unchanged.

- AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
- AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`

## Validation

989 pytest passed, 3 skipped, 5 subtests passed; 329 unittest passed, 1 skipped.
