# Direct unbound identifier semantic validation — v2.93

v2.93 activates a conservative subset of the frozen AJ static semantic rule that identifiers must be declared or assigned before they are read.

## Enforced direct-read forms

```text
x <- missingValue
RETURN missingResult
OUTPUT missingValue
```

These fail static semantic analysis unless the bare value identifier is already bound in the visible scope.

Valid bindings include function/method parameters, prior direct assignments and visible enclosing-scope bindings. The parser does not treat a comment describing a future computation as a declaration.

## Not broadened in this release

Compound-expression definite-assignment analysis is intentionally deferred. This release does not claim to detect every possible unbound identifier nested within indexing, member access, arithmetic or branch-flow expressions.

## Compatibility sentinel

Bare `NULL` remains accepted as an existing compatibility sentinel. This is not a dialect addition: AJ_24038155 v1.1 remains frozen and its canonical null literal is `NONE`.
