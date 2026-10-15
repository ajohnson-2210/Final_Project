# Bare CALL-argument binding semantics — v3.13

## Decision

AJ_24038155 Dialect v1.1 requires an identifier to be declared or assigned before it is read. Earlier pipeline releases enforced a deliberately conservative direct-read subset and explicitly deferred full compound-expression definite-assignment analysis.

v3.13 adds one independently audited category to that subset: an immediate bare `IdentifierNode` supplied as a value argument to `CALL routine(...)`.

Example accepted:

```text
FUNCTION demo ACCEPTS(value)
    copy <- value
    result <- CALL external(value, copy)
    RETURN result
ENDFUNCTION
```

Example rejected:

```text
FUNCTION demo ACCEPTS(value)
    result <- CALL external(value, missing)
    RETURN result
ENDFUNCTION
```

`missing` is an ordinary value read and must already be bound.

## Boundaries

The change is intentionally narrow.

- `CallNode.name` remains routine syntax and is not validated as a value identifier. Undefined external routine names therefore remain governed by the existing abstract/undefined-routine policy.
- Immediate bare arguments are checked.
- Nested `CALL` expressions are visited and apply the same immediate-argument rule to their own arguments.
- Compound arguments such as `CALL f(value + unresolved)` remain outside the v3.13 rule.
- Member-call argument semantics such as `object.process(unresolved)` are not broadened by this change.
- No parameter, assignment, import, external function, or algorithmic behaviour is synthesised.

The change is static-semantic validation only. It does not alter pseudocode normalisation or Python compilation.
