# NL-FDEP v3.10 release record

## Scope

v3.10 adds approved generic GC211 recovery for the omitted-`IS` non-empty predicate surface:

```text
identifier NOT EMPTY
```

which canonicalises to:

```text
LENGTH OF identifier > 0
```

This resolves source_f Algorithm 26 without changing its algorithm or inventing tree behaviour.

## Production change

`pseudocode_profiles.py` adds GC211 in the generic obvious-mismatch normaliser. The rule is simple-identifier, exact-phrase, quote/comment-safe, and case-insensitive.

The pre-existing explicit form `identifier IS NOT EMPTY` remains on its existing path.

## Regression boundary

Positive regressions cover:

- exact source_f Algorithm 26;
- generic simple identifiers;
- case-insensitive spelling;
- composition inside a larger condition.

Negative regressions preserve:

- `NOT BLANK`, `NOT NULL`, `NOT WHITESPACE`, `NOT MISSING`;
- existing `IS NOT EMPTY` ownership;
- member expressions and longer identifiers;
- strings and comments;
- the GC136 requirement for explicit backing before deque-specific front/back recovery.

## Dialect

AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## Validation

Working tree:

- pytest: **563 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**

Fresh extraction from packaged ZIP:

- pytest: **563 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
