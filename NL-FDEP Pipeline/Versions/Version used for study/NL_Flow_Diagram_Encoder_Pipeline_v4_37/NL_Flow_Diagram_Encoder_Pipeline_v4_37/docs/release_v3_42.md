# NL-FDEP v3.42 release record

## Scope

v3.42 implements the approved source_d Algorithm 37 member-indexed assignment-surface recovery while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC242 member-indexed lvalue assignment recovery

A Python-style single assignment equals on an explicit member-index lvalue is represented with the existing AJ assignment operator:

```text
object.member[index] = value
```

becomes:

```text
object.member[index] <- value
```

The rule changes only the assignment token. The object/member path, index expression, and right-hand value are preserved. It runs before the ordinary GC026 assignment recovery because GC026 intentionally handled only plain identifiers, index-only targets, and dotted member targets, not indexing after a member path.

The equals guard excludes `==`, `!=`, `<=`, and `>=`, and plain/index-only/member-only assignments remain on their established GC026 path.

Together with the user-approved GC240 preallocation rule and GC241 contextual class-routine recovery, source_d Algorithm 37 now parses, compiles, and executes as the supplied fixed-capacity stack. The generated backing storage is `[None] * capacity`; no stack algorithm or class semantics are invented by GC242.

## Validation

- targeted GC241/GC242 regression and boundary tests: 9 passed;
- full pytest suite: 762 passed, 3 skipped, 5 subtests passed;
- full unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 762 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
