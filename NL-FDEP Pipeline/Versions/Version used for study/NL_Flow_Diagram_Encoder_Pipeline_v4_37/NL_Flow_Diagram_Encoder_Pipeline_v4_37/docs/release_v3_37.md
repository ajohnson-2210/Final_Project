# NL-FDEP v3.37 release record

## Scope

v3.37 implements the approved early inline `//` comment interpretation fix while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC236 early inline slash-comment detachment

Text following an unquoted `//` on an executable source line is explanatory comment text and must not participate in compatibility interpretation. GC236 therefore detaches the executable prefix before declaration/literal/collection normalisation and retains the comment as a standalone `// ...` source line for the existing GC074 conversion to non-executable `COMMENT` metadata.

For example:

```text
deque = empty DoubleEndedQueue // Stores indices
```

is interpreted as the executable declaration plus comment metadata, allowing the existing collection rules to produce:

```text
deque <- EMPTY LIST
COMMENT Stores indices
```

The delimiter is quote-aware: `//` inside quoted strings remains literal string content. Full-line `// ...` comments retain their existing behaviour. The later GC135 fallback was aligned to the same quote-aware boundary so it cannot truncate a string containing `//`.

No deque front/back operation semantics are added by v3.37. source_d Algorithm 28 therefore advances past the contaminated declaration, while its separate `REMOVE FRONT FROM`, `REMOVE BACK FROM`, and `ADD BACK` operation surfaces remain visible for independent classification.

## Validation

- targeted GC236 regression/boundary tests: 3 passed;
- related existing comment/deque regressions: passed;
- full pytest suite: 740 passed, 3 skipped, 5 subtests passed;
- unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 740 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
