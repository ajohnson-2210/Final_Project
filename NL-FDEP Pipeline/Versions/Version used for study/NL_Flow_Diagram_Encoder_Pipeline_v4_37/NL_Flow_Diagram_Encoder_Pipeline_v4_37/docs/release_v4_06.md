# v4.06 — AJ dictionary GET missing-key semantics and JOIN compatibility

v4.06 fixes the compiler boundary for AJ v1.2 dictionary retrieval and packages the validated JOIN static-semantic rule accumulated after v4.05.

## Dictionary GET missing-key semantics

AJ v1.2 distinguishes one-argument and defaulted dictionary retrieval:

- `dictionary.GET(key)` must produce a runtime error when the key is missing;
- `dictionary.GET(key, default_value)` returns the supplied default when the key is missing.

v4.05 lowered both forms through Python `dict.get`, causing the one-argument form to return `None` rather than preserving AJ's missing-key error. v4.06 now lowers:

```text
dictionary.GET(key)          -> dictionary[key]
dictionary.GET(key, default) -> dictionary.get(key, default)
```

The same rule applies to legacy `~GET` syntax when it reaches the compatibility parser. Unknown receivers remain ordinary user-defined method calls; GET is not assumed to be dictionary retrieval by spelling alone.

## JOIN static compatibility

AJ does not specify implicit stringification for `JOIN(collection, separator)`. The static validator therefore does not invent conversion semantics. When types are statically known:

- the separator must be STRING/CHAR-compatible;
- known homogeneous collection elements must be STRING/CHAR-compatible;
- known numeric/non-text elements are rejected;
- unknown or mixed element types remain unresolved rather than guessed.

This does not alter any successfully canonicalised study case; the corpus JOIN occurrence is a character-collection join.

## Dialect impact

None. AJ dialect v1.1 and v1.2 source documents are unchanged.

- AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
- AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`

## Validation

1141 pytest passed, 3 skipped, 5 subtests passed; 332 unittest passed, 1 skipped.
