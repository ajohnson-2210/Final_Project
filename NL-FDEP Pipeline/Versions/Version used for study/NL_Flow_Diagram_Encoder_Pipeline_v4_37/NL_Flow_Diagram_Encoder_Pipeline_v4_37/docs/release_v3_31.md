# NL-FDEP v3.31 release record

## Scope

v3.31 implements the approved source_d Algorithm 5 quoted-set-literal compatibility recovery while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC231 quoted scalar set-literal recovery

source_d Algorithm 5 supplies its punctuation collection explicitly as a non-empty Python-style brace set whose elements are all quoted string scalars, including escaped apostrophe and double-quote values. Before v3.31, the later raw-string compatibility pass could corrupt that quoted brace surface before strict AJ parsing.

GC231 activates only when the complete assignment RHS parses as a non-empty Python set literal and every member is a string scalar. Each member is rendered as an AJ `STRING(...)` literal and the complete collection is routed through the existing compatibility intrinsics:

```text
name <- CALL to_set(CALL list_value(STRING("."), STRING(","), ...))
```

This representation avoids changing the frozen AJ parser while preserving the explicitly supplied set semantics. It also prevents the later raw-string wrapper from reinterpreting embedded quote characters.

GC231 deliberately refuses:

- dictionary literals;
- empty braces;
- mixed or unquoted set members;
- set comprehensions;
- string scalar values containing control characters outside the frozen AJ string escape surface.

No punctuation predicate is inferred: the only members used are the values explicitly present in the source literal.

## source_d Algorithm 5

The supplied `RemovePunctuation` routine now canonicalises its explicit punctuation set, parses, encodes to a flow diagram, compiles deterministically to Python `set([...])`, and executes with the supplied membership-removal behaviour. Apostrophe and double-quote punctuation members are preserved.

## Validation

- targeted source_d 5 / GC231 regression and refusal-boundary tests: 7 passed;
- full pytest suite: 715 passed, 3 skipped, 5 subtests passed;
- unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 715 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
