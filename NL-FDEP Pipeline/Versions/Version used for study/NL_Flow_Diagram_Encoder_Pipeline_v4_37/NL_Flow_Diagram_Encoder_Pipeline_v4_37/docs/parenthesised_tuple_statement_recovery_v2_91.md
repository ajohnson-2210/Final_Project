# Corpus-wide parenthesised multi-value statement recovery — v2.91

## Problem

Generic pseudocode commonly writes multiple returned or output values with an outer pair of parentheses:

```text
RETURN (a, b)
OUTPUT (a, b)
```

AJ_24038155 v1.1 represents the same values explicitly as a tuple expression. Earlier processing recognised unparenthesised `RETURN a, b` / `OUTPUT a, b`, but the outer parentheses hid the comma from the top-level splitter and could allow `RETURN` to be misclassified by generic free-call prefixing.

## General rule

One outer pair of parentheses may be unwrapped only for the purpose of detecting multiple top-level values. If there are at least two values, canonicalise to `TUPLE(...)`. Otherwise preserve the grouping.

Positive examples:

```text
RETURN (a, b) -> RETURN TUPLE(a, b)
OUTPUT (a, b) -> OUTPUT TUPLE(a, b)
```

Negative examples:

```text
RETURN (a + b)          # grouped expression, not tuple recovery
RETURN (combine(a, b))  # comma is inside a nested call
```

The splitter remains quote-, escape-, and nesting-aware.

## Keyword protection

GC083 must not prefix AJ statement keywords as routine calls. `RETURN` is now included in the protected keyword set; `OUTPUT` remains protected.

The historical `CALL RETURN(...)` repair remains accepted for backwards compatibility, but new input no longer needs to pass through that mangled intermediate representation.

## Scope

This is a representational compatibility correction only. It does not add a dialect construct, infer additional values, alter control flow, or depend on any model/file/algorithm identity.


## v3.72 clarification

Only an explicitly parenthesised output tuple remains tuple data. A bare comma-separated `OUTPUT a, b` is now distinguished as multiple output arguments and canonicalises to `OUTPUT CALL output_values(a, b)`, compiling to `print(a, b)`. Multi-value `RETURN` remains tuple recovery.
