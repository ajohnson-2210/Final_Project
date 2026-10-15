# NL-FDEP v3.33 release record

## Scope

v3.33 implements the approved source_d Algorithm 11 evidence-based set-to-list conversion recovery while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC232 evidenced set-to-list conversion

source_d Algorithm 11 explicitly creates an empty set, adds each IP address to that set, and finally calls `ConvertSetToList(unique_set)`. Before v3.33, the generic call-prefix recovery preserved that final operation only as an unresolved ordinary call, so deterministic Python compilation produced an undefined `ConvertSetToList(...)` function.

GC232 recognises only the exact free one-argument form `ConvertSetToList(name)` after ordinary compatibility recovery has made the source representation explicit. The argument must have been initialised as `EMPTY SET` earlier in the same lexical routine, and a later direct reassignment removes that evidence. Under those safeguards, the call is represented using the existing compatibility intrinsic:

```text
CALL to_list(name)
```

which already lowers deterministically to Python:

```python
list(name)
```

GC232 deliberately refuses unproven identifiers, evidence from another function/method/constructor, forward-only set evidence, member calls, zero-argument calls, multi-argument calls, and identifiers whose set evidence was invalidated by direct reassignment. No ordering property is invented: the result has the ordinary iteration order of the source set conversion.

## source_d Algorithm 11

The supplied duplicate-IP routine now canonicalises its explicit set-to-list conversion, parses, encodes to a flow diagram, compiles deterministically to Python, and executes with the supplied uniqueness behaviour.

## Validation

- targeted source_d 11 / GC232 regression and refusal-boundary tests: 6 passed;
- full pytest suite: 725 passed, 3 skipped, 5 subtests passed;
- unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 725 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
