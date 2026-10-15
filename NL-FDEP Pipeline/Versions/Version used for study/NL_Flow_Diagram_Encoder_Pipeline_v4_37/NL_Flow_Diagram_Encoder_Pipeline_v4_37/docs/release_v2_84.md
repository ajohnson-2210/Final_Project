# NL-FDEP v2.84 release record

## Dialect baseline

v2.84 advances the active language baseline from **AJ_24038155 Dialect v1.0** to **AJ_24038155 Dialect v1.1**. The normative delta is recorded in `AJ_24038155_Dialect_v1_1.md`.

## Approved language changes

- native `NONE` literal, compiled to Python `None`;
- general member-method invocation `object.method(...)`;
- explicit distinction between `object.property` and `object.method()`;
- canonical dictionary retrieval `dictionary.GET(key[, default])`;
- type/evidence-based resolution of dictionary `GET`, so a user-defined non-dictionary `GET` method remains ordinary;
- backwards-compatible strict acceptance of v1.0 `dictionary~GET(...)`;
- compatibility-profile canonicalisation of legacy `~GET` to `.GET`;
- compatibility-profile canonicalisation of `None`/`none` to `NONE` outside quoted strings;
- generic CALL-prefix recovery no longer corrupts member calls by inserting `CALL` after a dot.

## Study evidence

source_b Algorithm 38 — First Non-Repeating Character — is the motivating empirical occurrence. Its audit is recorded in `source_b_algorithm38_dialect_v1_1_audit_v2_84.md`, and the exact source shape is retained in `tests/test_aj_v11_none_member_get_v2_84.py`.

## Behavioural result

The canonical v1.1 form compiles to the intended Python dictionary `.get(...)` operation and native `None` return without semantic inference or algorithmic reconstruction.

## Validation

Working-tree validation:

```text
pytest:
    317 passed
    3 skipped
    5 subtests passed

unittest:
    239 passed
    1 skipped
```

The packaged ZIP is smoke-tested after creation using the same suites.
