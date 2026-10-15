# Corpus-wide ASCII-to-CHAR representation recovery — v2.89

## Rule

Generic compatibility accepts both source shapes:

```text
ASCII(expression)
CALL ASCII(expression)
```

and canonicalises them to the existing representation:

```text
CHAR(expression)
```

The rule is case-insensitive on the source wrapper and source-shape independent.

## Why this is a representation rule

The pipeline already contained the canonical `CALL ASCII(x) -> CHAR(x)` compatibility mapping. The defect was ordering: raw `ASCII(x)` could reach generic call prefixing later and become `CALL ASCII(x)` only after the shared universal pass had already run. v2.89 makes the shared rule accept both forms directly.

No function name, algorithm number, model name, or corpus filename participates in the implementation.

## Reserved identifier interaction

AJ keywords are case-insensitive, so an identifier written as `char` collides lexically with the reserved `CHAR` token. The existing reversible reserved-identifier policy applies mechanically:

```text
char -> __reserved_keyword__char
```

Thus:

```text
ASCII(char)
```

becomes:

```text
CHAR(__reserved_keyword__char)
```

when `char` is being used as an identifier.

## Non-goals

The rule does not:

- recognise arbitrary character-code helper names;
- rewrite `characterCode(x)` or other free calls;
- modify AJ_24038155 Dialect v1.1;
- change collection size or representation;
- alter algorithm control flow.
