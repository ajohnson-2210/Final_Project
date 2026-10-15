# NL-FDEP v3.40 release record

## Scope

v3.40 implements the user-approved fixed-size-array initialisation rule identified during the source_d Algorithm 37 audit while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC240 NONE-filled fixed-array preallocation

For the exact unfilled source declaration:

```text
Array of size N
```

where `N` is a single identifier or non-negative integer literal, the project rule is now:

```text
Array of size N
-> CALL create_array(N, NONE)
-> Python [None] * N
```

This makes the source's fixed-size writable storage explicit without inventing a different fill value. The rule is user-confirmed. Existing declarations such as `Array of size N initialized to 0` remain governed by GC160 and retain their previous deterministic lowering. Complex or prose-qualified unfilled size expressions remain outside GC240.

The rule also recognises a dotted assignment target such as `self.arr` so the exact source_d 37 backing-array declaration is represented, but it does not repair unrelated legacy class/constructor/property syntax. Those boundaries remain independently visible.

## Validation

- targeted GC240 regression/boundary tests: 4 passed;
- full pytest suite: 753 passed, 3 skipped, 5 subtests passed;
- unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 753 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
