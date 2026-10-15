# NL-FDEP v3.39 release record

## Scope

v3.39 implements the approved explicit `ConvertToSet(value)` compatibility recovery for source_d Algorithm 34 while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC238 explicit set-conversion intrinsic recovery

For an exact free call with one balanced argument:

```text
ConvertToSet(value)
-> CALL to_set(value)
```

The mapping uses the pipeline's existing `to_set` compatibility intrinsic, which deterministically compiles to Python `set(value)`. Because the source itself explicitly requests set conversion, GC238 does not infer a collection type or invent deduplication semantics.

The recovery is expression-scoped and refuses routine declarations named `ConvertToSet`, member methods such as `obj.ConvertToSet(value)`, zero-argument calls, multi-argument calls, quoted text, and comments. Nested expressions inside the one explicit argument remain supported through the existing balanced-call scanner.

source_d Algorithm 34 now preserves both conversions supplied by the source: `ConvertToSet(list1)` is represented by GC238 and the existing evidence-gated `ConvertSetToList(result_set)` remains represented by GC232.

## Validation

- targeted GC238 regression/boundary tests: 4 passed;
- full pytest suite: 749 passed, 3 skipped, 5 subtests passed;
- unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 749 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
