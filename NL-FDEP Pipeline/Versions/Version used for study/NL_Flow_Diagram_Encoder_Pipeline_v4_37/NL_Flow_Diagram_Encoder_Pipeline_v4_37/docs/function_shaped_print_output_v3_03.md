# GC206 — function-shaped PRINT output recovery

## Rule

A standalone, case-insensitive, balanced single-expression form:

```text
PRINT(expression)
```

is canonicalised to:

```text
OUTPUT expression
```

## Boundary

GC206 is deliberately statement-shaped and narrow:

- the outer `PRINT(...)` call must occupy the whole non-whitespace line;
- exactly one non-empty top-level expression is accepted;
- nested parentheses and commas inside nested calls are preserved;
- commas inside quoted strings are preserved;
- `PRINT()` and top-level multi-argument `PRINT(a, b)` are not claimed;
- member calls such as `object.PRINT(value)` are not claimed;
- quoted/comment text containing `PRINT(...)` is not rewritten.

The rule does not add casts or infer variable types.

## Python output rendering

The existing compiler's `OUTPUT`-only message renderer may lower a pure `STRING + identifier + ...` message chain to a Python f-string. This is a target-language rendering choice, not a canonical-AJ rewrite. Ordinary concatenation used in assignments or other program logic remains ordinary concatenation.
