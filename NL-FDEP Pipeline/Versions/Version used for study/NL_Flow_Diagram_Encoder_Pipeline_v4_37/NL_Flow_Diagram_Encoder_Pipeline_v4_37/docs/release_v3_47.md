# NL-FDEP v3.47 release record

## Scope

v3.47 implements the approved source_d Algorithm 42 evidenced tuple-in-set-insertion recovery while leaving frozen AJ_24038155 Dialect v1.1 unchanged.

## GC248 evidenced two-value tuple set insertion

When a receiver is independently evidenced as set-backed by an explicit `EMPTY SET` declaration and the existing collection normaliser has preserved a source insertion as:

```text
CALL add_to_set(pairs, (a, b))
```

GC248 recognises the inserted value only when it is one outer parenthesis pair containing exactly two top-level expressions. The compatibility representation is:

```text
CALL add_to_set(pairs, TUPLE(a, b))
```

This completes the ordering path exposed by source_d Algorithm 42, where the source explicitly inserts `(MIN(num, complement), MAX(num, complement))` into a set. Existing MIN/MAX recovery continues unchanged, producing:

```text
CALL add_to_set(pairs, TUPLE(CALL min(num, complement), CALL max(num, complement)))
```

The rule does not infer tuple meaning for grouped single expressions, unproven receivers, or non-two-value parenthesised payloads. It adds no set, tuple, parser, or compiler semantics.

## Validation

- targeted GC248 regression and refusal-boundary tests: 5 passed;
- full pytest suite: 788 passed, 3 skipped, 5 subtests passed;
- full unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 788 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
