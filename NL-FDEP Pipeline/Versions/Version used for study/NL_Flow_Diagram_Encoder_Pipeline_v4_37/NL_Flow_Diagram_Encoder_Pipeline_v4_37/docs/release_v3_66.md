# Release v3.66 — retire GC160 inferred string-to-character-list input conversion

## Scope

This release retires GC160's inferred conversion of an externally supplied text input from a string into a character list merely because the value is subsequently indexed and used with `LENGTH OF`.

## Retired GC160 behaviour

Earlier releases treated a text-like input such as:

```text
text <- INPUT(STRING("Enter text"))
first <- text[0]
OUTPUT LENGTH OF text
```

as sufficient evidence to rewrite the input to:

```text
text <- CALL list_from_string(INPUT(STRING("Enter text")))
```

and therefore to Python `list(input(...))`.

That conversion is not source-established. Indexing and length are valid operations on strings, and converting the value into a list changes its representation and return type. Variable names or prompt words such as `text`, `string`, `sentence`, or `paragraph` do not justify that algorithmic type conversion.

v3.66 therefore preserves the original `INPUT(...)` representation unless the source explicitly requests conversion.

## Input-resolution alignment

The evidence-scoring helper no longer reports `STRING_TO_LIST_OF_CHARACTER` as a deterministic conversion for text-like inputs that are only indexed and measured by length. Such use is now recorded as string-compatible and the explicit input is preserved.

## Preserved behaviour

Explicit source conversion remains available. For example:

```text
characters <- CALL list_from_string(text)
```

continues to compile deterministically to Python `list(text)`.

The separate neutral unnamed-wrapper policy remains unchanged: top-level external inputs may still be represented as wrapper parameters when that existing policy applies. That is not a string-to-list conversion.

## Validation

- focused GC160/input-resolution boundary gate: 6 passed;
- full pytest gate: 888 passed, 3 skipped, 5 subtests passed;
- full unittest gate: 301 passed, 1 skipped;
- frozen AJ_24038155 Dialect v1.1 SHA-256 unchanged: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

No parser, compiler, intrinsic, or frozen AJ_24038155 Dialect v1.1 syntax change in v3.66.
