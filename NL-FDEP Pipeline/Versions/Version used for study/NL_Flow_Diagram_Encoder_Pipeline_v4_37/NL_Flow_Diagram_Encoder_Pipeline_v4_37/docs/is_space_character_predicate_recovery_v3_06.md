# GC207 — exact `is space` character predicate recovery

## Rule

In generic compatibility input only, the exact source predicate:

```text
identifier is space
```

is represented canonically as:

```text
identifier == CHAR(" ")
```

The match is case-insensitive and may occur inside a larger condition. It is identifier-based and corpus/model/algorithm independent.

## Deliberate exclusions

GC207 does not reinterpret:

- `is whitespace`
- `is blank`
- `is empty`
- `is a space`
- text inside quoted strings
- `COMMENT` payloads
- text after an unquoted `#` inline-comment marker

The distinction matters because a single U+0020 space character is narrower than general whitespace or descriptive blank/empty concepts.

## Semantics

No helper, import, typecast, algorithm step, or domain behaviour is invented. Python lowering follows the frozen AJ `CHAR(" ")` literal semantics and becomes the ordinary string character `' '`.
