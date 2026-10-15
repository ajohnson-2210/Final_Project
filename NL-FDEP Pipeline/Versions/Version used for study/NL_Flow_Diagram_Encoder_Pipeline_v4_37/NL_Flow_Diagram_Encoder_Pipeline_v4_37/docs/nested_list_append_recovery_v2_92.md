# Corpus-wide nested list `.append(...)` canonicalisation — v2.92

## Rule

AJ v1.1 canonically expresses list append as:

```text
APPEND value TO collection
```

Python-like pseudocode often writes:

```text
collection.append(value)
```

The long-standing GC033 rule already canonicalises simple arguments. v2.92 adds GC200 for the ordering case where the explicit append argument itself contains nested parentheses and GC033 cannot match it.

GC200 is deliberately evidence-backed. It requires direct LIST evidence for the simple receiver identifier, such as:

```text
items <- EMPTY LIST
items <- LIST [...]
items <- CALL list_value(...)
items AS LIST
```

Only then may a balanced standalone expression:

```text
items.append(nested(expression))
```

become:

```text
APPEND nested(expression) TO items
```

## Boundaries

- No model name, corpus filename, algorithm number or wrapper function participates in the rule.
- No receiver is inferred to be a list merely because it has a method named `append`.
- Nested parentheses and quoted parentheses are balanced rather than truncated by regex.
- Existing simple GC033 behaviour remains intact.
- AJ_24038155 Dialect v1.1 is frozen and unchanged.
