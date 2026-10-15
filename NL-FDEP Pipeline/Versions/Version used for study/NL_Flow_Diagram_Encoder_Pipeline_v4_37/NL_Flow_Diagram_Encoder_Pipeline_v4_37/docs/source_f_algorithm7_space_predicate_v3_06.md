# source_f Algorithm 7 audit evidence — v3.06

## Source occurrence

```text
INPUT sentence

words = []
current = ""

FOR each char in sentence:
    IF char is space:
        IF current != "":
            words.append(current)
            current = ""
    ELSE:
        current += char

IF current != "":
    words.append(current)

RETURN words
```

The v3.05 source_f adapter preserves this multiline structure. The remaining source-surface issue is the exact predicate `char is space`.

## Approved recovery

`<identifier> is space` is an exact single-space-character predicate and is canonicalised as:

```text
<identifier> == CHAR(" ")
```

For this occurrence, the reserved AJ keyword collision is independently handled by the established `__reserved_keyword__` mechanism, yielding:

```text
IF __reserved_keyword__char == CHAR(" ") THEN
```

## Boundary

The rule does not broaden `space` to whitespace and does not recover `is whitespace`, `is blank`, `is empty`, or `is a space`. Quoted strings and comments are not rewritten.

- semantic inference: **NO NEW SEMANTIC INFERENCE**
- algorithmic reconstruction: **NO**
- source logic correction: **NO**
- dialect change: **NO**
