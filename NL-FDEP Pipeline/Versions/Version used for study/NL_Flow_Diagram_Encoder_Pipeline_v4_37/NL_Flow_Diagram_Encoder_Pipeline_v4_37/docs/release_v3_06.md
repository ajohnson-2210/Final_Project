# NL-FDEP v3.06 release record

## Scope

v3.06 implements the approved exact single-space-character predicate recovery motivated by source_f Algorithm 7.

## Production change

GC207 recovers the generic compatibility surface:

```text
identifier is space
```

as:

```text
identifier == CHAR(" ")
```

The rule is case-insensitive, identifier-name independent, and applies outside quoted strings/comments only. It does not broaden to whitespace/blank/empty semantics.

## source_f Algorithm 7

The v3.05 adapter-preserved source now canonicalises the branch condition to:

```text
IF __reserved_keyword__char == CHAR(" ") THEN
```

The remainder of the split-into-words algorithm uses existing list, string, append, loop, reserved-keyword, parser, and compiler behaviour unchanged.

## Audit boundary

- semantic inference: **NO NEW SEMANTIC INFERENCE**
- algorithmic reconstruction: **NO**
- source logic correction: **NO**
- whitespace broadening: **NO**
- dialect change: **NO**

## Dialect

AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## Validation

Working tree:

- pytest: **510 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**

Fresh extraction from packaged ZIP:

- pytest: **510 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
