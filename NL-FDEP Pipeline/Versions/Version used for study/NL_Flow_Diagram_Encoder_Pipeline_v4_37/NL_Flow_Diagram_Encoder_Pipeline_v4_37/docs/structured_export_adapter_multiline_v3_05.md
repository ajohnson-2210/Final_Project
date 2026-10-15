# source_f structured-corpus adapter audit — v3.05

## Motivating study occurrence

The current source_f corpus already preserves task boundaries and indentation:

```text
# Split Sentence into Words

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

The pre-v3.05 source_f adapter was designed for a compressed export. It used every `INPUT`, `INIT`, or `FUNCTION` line as a possible item start, stripped indentation, and joined body lines with spaces. On the current structured corpus this destroyed source formatting that was already available and could split nested constructs into false corpus items.

## Approved adapter correction

When column-one `# <title>` headings are present, `StructuredExportAdapter` now treats those headings as the corpus item boundaries and preserves the body as multiline source, including relative indentation and internal blank lines.

The legacy compressed extraction path remains available as a fallback when no hash-heading structure is present.

Indented hash comments are not task boundaries.

## Boundary

This is a corpus-extraction correction only.

```text
semantic inference: NO
algorithmic reconstruction: NO
pseudocode-language recovery: NO
source correction: NO
corpus extraction correction: YES
dialect change: NO
```

The adapter does not attempt to repair source_f Algorithm 7's separate `char is space` representation. That remains the next audit decision after faithful extraction.

AJ_24038155 Dialect v1.1 remains frozen and unchanged.
