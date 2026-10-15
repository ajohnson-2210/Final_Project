# v4.01 — flow-sensitive collection representation tracking

v4.01 makes compiler collection representation evidence follow source execution
order within each lexical scope.

## Compiler change

Earlier releases correctly isolated collection evidence by lexical scope, but a
name was still treated as SET-backed for the entire scope once any `EMPTY SET`
assignment appeared there.  A later reassignment to `EMPTY LIST` could therefore
leave a stale `.add(...)` lowering.

v4.01 updates collection evidence as assignments are emitted:

- `EMPTY SET` and explicit `to_set(...)` establish SET backing;
- `EMPTY LIST`, list literals, `to_list(...)`, and `to_array(...)` establish
  non-SET/list backing;
- any other reassignment clears stale SET evidence rather than guessing;
- later assignments do not retroactively affect earlier APPEND operations.

Equivalent evidence is merged conservatively across IF/ELSE, loops, and
TRY/CATCH: SET backing is retained after control flow only when every possible
path agrees. Loop variables and named CATCH bindings clear same-named collection
hints for their bound scope, and a nested function declaration clears stale SET
evidence for its own bound name.

Example:

```text
FUNCTION reset ACCEPTS()
    result <- EMPTY SET
    APPEND 1 TO result
    result <- EMPTY LIST
    APPEND 2 TO result
    RETURN result
ENDFUNCTION
```

now compiles with `result.add(1)` followed by `result.append(2)`.

## Dialect impact

None. AJ dialect v1.1 and v1.2 source documents are unchanged.

- AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
- AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`

## Validation

1015 pytest passed, 3 skipped, 5 subtests passed; 332 unittest passed, 1 skipped.
