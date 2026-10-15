# v3.94 — punctuation predicate compiler boundary

v3.94 removes the compiler-owned semantic definition of `is_punctuation(value)`.

The audit established that a bare punctuation predicate is not equivalent to a single Python intrinsic: different source responses provide different punctuation sets or regex definitions, and an undefined predicate requires an explicitly supplied/imported helper rather than compiler-invented semantics.

## Compiler change

Previously, canonical:

```text
CALL is_punctuation(value)
```

was lowered to a compiler-selected predicate equivalent to:

```python
not str(value).isalnum() and not str(value).isspace()
```

That lowering has been removed. The call now follows ordinary call compilation:

```python
is_punctuation(value)
```

Therefore an explicit source/helper definition remains authoritative, while an undefined dependency remains unresolved at execution rather than being silently assigned a punctuation policy by the compiler.

`is_digit(value)` and `is_uppercase(value)` remain compiler intrinsics because they correspond directly to singular Python character predicates (`.isdigit()` and `.isupper()`).

## Dialect impact

None. AJ dialect v1.2 is unchanged.

## Validation

983 pytest passed, 3 skipped, 5 subtests passed; 327 unittest passed, 1 skipped.
