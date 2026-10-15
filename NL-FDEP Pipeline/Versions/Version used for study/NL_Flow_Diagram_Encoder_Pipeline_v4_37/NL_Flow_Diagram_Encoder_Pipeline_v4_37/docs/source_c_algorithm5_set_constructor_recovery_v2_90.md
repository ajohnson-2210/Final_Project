# source_c Algorithm 5 — set-constructor recovery — v2.90

## Motivating occurrence

```text
FUNCTION removePunctuation(sentence):
    punctuation = set(". , ! ? ; : ' \" - ( ) [ ] { }")
    result = ""
    FOR each char in sentence:
        IF char NOT IN punctuation:
            result = result + char
    RETURN result
```

## Finding

The algorithm explicitly supplies a set-construction operation. v2.89 already had the general canonical mapping `CALL set(value) -> CALL to_set(value)`, but raw `set(value)` could acquire the `CALL` prefix only after that rule had run. The failure was therefore pipeline ordering/source shape, not missing semantics.

## Approved recovery

Both raw and already-prefixed constructor forms are normalised through the same existing compatibility representation:

```text
set(value)
CALL set(value)
```

when used as an assignment RHS become:

```text
CALL to_set(value)
```

The compiler lowers `CALL to_set(value)` to Python `set(value)`.

The implementation does not inspect the model name, corpus filename, algorithm number, function name, or punctuation-specific content.

## Source semantics deliberately preserved

The source string contains literal spaces between punctuation marks. Python `set(...)` therefore includes the space character in the set, and the supplied algorithm removes spaces as well as punctuation. v2.90 deliberately preserves that behaviour. Changing the string would be a source-logic repair rather than representational recovery.

## Classification

```text
status: PASS AFTER CONSERVATIVE SET-CONSTRUCTOR RECOVERY
semantic inference: NO
algorithmic reconstruction: NO
source logic correction: NO
dialect change: NO — AJ_24038155 Dialect v1.1 remains frozen
```
