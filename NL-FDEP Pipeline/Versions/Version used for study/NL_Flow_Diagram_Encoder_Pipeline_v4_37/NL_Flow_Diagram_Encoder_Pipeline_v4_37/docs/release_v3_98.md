# v3.98 — lexical collection-type scope isolation

v3.98 fixes a compiler semantic defect in collection representation tracking.
Set evidence is no longer shared program-wide merely because two independent
variables have the same identifier spelling.

## Compiler change

Previously, if any function contained an assignment such as:

```text
result <- EMPTY SET
```

then every `APPEND ... TO result` in the structured program could be emitted as
`result.add(...)`, including a different function whose local `result` was
explicitly `EMPTY LIST`.

Collection backing is now tracked by lexical scope:

- sibling functions/methods do not share local collection-type evidence;
- parameters and local assignments shadow enclosing evidence;
- an unshadowed enclosing collection remains visible to a nested function;
- explicit `EMPTY SET` still lowers `APPEND` to `.add()`;
- list-backed `APPEND` lowers to `.append()`.

This preserves AJ function scope and the source-supplied collection
representation instead of conflating same-spelled locals.

## Included validated working-tree changes

These changes were previously validated but intentionally not packaged because
they did not alter the compiler:

1. **Single-file numbered title metadata** — a leading `1. <title>` line is
   treated as study metadata when the following non-blank line clearly starts
   pseudocode, matching the existing `#<title>` study-file form. Numbered prose
   followed by prose is not stripped.
2. **INTEGER DIVISION negative-semantics audit note** — AJ `INTEGER DIVISION`
   remains mapped to Python `//`. The audit records truncation toward zero as
   the alternative convention and documents the expected divergence for
   negative, non-exact quotients and the corresponding `MODULUS` result.

## Dialect impact

None. AJ dialect v1.1 and v1.2 source documents are unchanged.

- AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
- AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`

## Validation

997 pytest passed, 3 skipped, 5 subtests passed; 332 unittest passed, 1 skipped.
