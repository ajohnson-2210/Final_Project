# Release v3.72 — multi-value OUTPUT preserves argument semantics

## Problem

The generic GC081 compatibility rule previously collapsed both of these different source surfaces into tuple data:

```text
OUTPUT a, b
OUTPUT (a, b)
```

Both became:

```text
OUTPUT TUPLE(a, b)
```

which made Python emit `print((a, b))`. The bare comma-separated form supplies multiple output components; it does not explicitly construct tuple data.

## Change

Bare comma-separated source output now canonicalises to the output-only compatibility intrinsic:

```text
OUTPUT CALL output_values(a, b)
```

The Python output renderer lowers that exact intrinsic to:

```python
print(a, b)
```

Parenthesised and explicit tuple output remain tuple data:

```text
OUTPUT (a, b)       -> OUTPUT TUPLE(a, b)
OUTPUT TUPLE(a, b)  -> OUTPUT TUPLE(a, b)
```

and compile to `print((a, b))`.

source_a Algorithm 42's GC169 canonical replacement now uses the same output-specific representation. GC175's message interpolation behaviour is unchanged.

## Validation

- pytest: 903 passed, 3 skipped, 5 subtests passed
- unittest: 303 passed, 1 skipped
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
