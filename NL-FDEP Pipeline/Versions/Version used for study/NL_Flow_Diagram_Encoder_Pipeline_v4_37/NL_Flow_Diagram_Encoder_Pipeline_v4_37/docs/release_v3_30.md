# NL-FDEP v3.30 release record

## Scope

v3.30 implements the approved source_c Algorithm 19 boundary fix while leaving the frozen AJ_24038155 Dialect v1.1 unchanged and introducing no new compatibility meaning.

## GC051 standalone `SWAP(...)` boundary fix

GC051 exists to recover the standalone procedural shorthand:

```text
SWAP(a, b)
```

as the existing SWAP statement form. In v3.29 its unanchored regular expression could also match the `swap(a, b)` substring inside a function declaration such as:

```text
FUNCTION swap(a, b):
```

Because identifiers are case-sensitive in AJ v1.1, rewriting that declaration to an uppercase `SWAP` routine name did not preserve the supplied source identifier.

v3.30 restricts GC051 to a complete standalone source line (apart from indentation and line ending). Consequently:

```text
FUNCTION swap(a, b):
```

continues through the ordinary function-header compatibility path and becomes:

```text
FUNCTION swap ACCEPTS(a, b)
```

while a genuine standalone:

```text
SWAP(a, b)
```

continues to receive the existing SWAP statement lowering. `CALL swap(a, b)`, `obj.swap(a, b)`, assignments, and other embedded occurrences are not reclassified by GC051.

## source_c Algorithm 19

The supplied arithmetic swap routine now preserves its lowercase `swap` identifier, parses and compiles deterministically, and executes with the supplied `(a, b) -> (b, a)` behaviour.

## Validation

- targeted source_c 19 / GC051 regression and boundary tests: pass;
- full pytest suite: 708 passed, 3 skipped, 5 subtests passed;
- unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 708 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
