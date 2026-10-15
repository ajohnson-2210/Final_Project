# NL-FDEP v3.13 release record

## Scope

v3.13 implements the approved static-semantic correction identified while auditing source_f Algorithm 30. It extends the existing conservative declared/assigned-before-read validator to immediate bare value identifiers used as arguments to `CALL routine(...)`.

## Production change

`aj_parser.py` now validates immediate bare `IdentifierNode` arguments for `CallNode` expressions against the currently visible binding set.

For example:

```text
result <- CALL external(boundValue, missingValue)
```

now fails static semantic analysis when `missingValue` is not a parameter, prior assignment, or otherwise visible binding.

The called routine name remains syntax rather than a value read. Therefore:

```text
result <- CALL undefinedExternal(boundValue)
```

remains syntactically and statically acceptable under the existing undefined-routine policy.

Nested `CALL` expressions apply the same immediate-argument rule to their own arguments. Full compound-expression definite-assignment analysis remains deliberately deferred; for example, v3.13 does not newly reject `CALL external(boundValue + unresolved)`. Member-call argument validation is likewise outside this approved change.

## source_f Algorithm 30

The exact source uses:

```text
topics = applyLDA(dtm, numTopics)
```

while declaring only `corpus` as input and never assigning `numTopics`. Generic compatibility processing continues to recover the source structurally without synthesising data. Static semantic analysis now correctly rejects the resulting `CALL applyLDA(dtm, numTopics)` because `numTopics` is an unbound value identifier.

The algorithm also depends on undefined high-level routines `preprocess`, `buildDocumentTermMatrix`, `applyLDA`, and `extractTopWords`. These remain source-level abstract dependencies and are not implemented by the pipeline.

Classification:

**EXPECTED FAIL — ABSTRACT / UNDEFINED ROUTINE DEPENDENCIES + UNBOUND SOURCE IDENTIFIER**.

## Dialect

AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## Validation

Working tree after the v3.13 change:

- pytest: **587 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`

Fresh extraction from packaged ZIP:

- pytest: **587 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
