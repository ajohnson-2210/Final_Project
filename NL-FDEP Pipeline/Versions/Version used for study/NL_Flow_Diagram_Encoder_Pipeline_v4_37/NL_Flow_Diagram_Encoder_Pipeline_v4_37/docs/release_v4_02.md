# v4.02 — termination-aware collection flow and semantic-validator refinements

v4.02 extends the flow-sensitive compiler work from v4.01 so collection
representation evidence is merged only across control-flow paths that can
actually reach the following statement.

## Compiler change

Earlier flow-sensitive tracking still included `RETURN`/`RAISE` branches when
merging SET evidence after an `IF`.  That could erase the only representation
on the continuing path and generate `.append(...)` for a value that is known to
be SET-backed whenever execution reaches that statement.

v4.02 now:

- excludes `IF`/`ELSE IF`/`ELSE` branches that definitely `RETURN` or `RAISE`
  from the post-`IF` collection-state merge;
- recognises nested all-terminating `IF`/`TRY` blocks for the same purpose;
- keeps the zero-iteration path for `WHILE`, `FOR EACH`, and RANGE loops, while
  ignoring an always-terminating loop-body state that can never reach the code
  after the loop; and
- merges `TRY/CATCH` using only the normal and caught-error paths that can reach
  `ENDTRY`, instead of treating the pre-`TRY` representation as an additional
  post-state; and
- tracks `BREAK` and `CONTINUE` states explicitly for the innermost loop, so an
  abrupt branch does not influence statements it cannot reach, while break/continue
  states still participate conservatively in the representation visible when the
  loop eventually exits. Nested-loop breaks remain scoped to the inner loop.

The analysis remains deliberately representation-focused; it does not invent
collection types when different reachable loop-exit paths disagree.

Example:

```text
FUNCTION demo ACCEPTS(flag)
    x <- EMPTY LIST
    IF flag THEN
        RETURN NONE
    ELSE
        x <- EMPTY SET
    ENDIF
    APPEND 1 TO x
    RETURN x
ENDFUNCTION
```

The only path reaching `APPEND` has SET-backed `x`, so v4.02 correctly emits
`x.add(1)`.

## Packaged static-semantic refinements since v4.01

These changes were validated in the working tree but were not independently
packaged because they did not modify the Python compiler.

### Conservative definite assignment

The existing AJ v1.2 direct/bare identifier check now respects structural
control flow:

- a new binding after `IF` survives only when every possible fallthrough branch
  establishes it;
- assignments introduced only inside potentially zero-iteration loops do not
  escape those loops;
- `TRY/CATCH` retains a new binding only when both normal and caught-error paths
  establish it; and
- named catch variables do not leak after `ENDTRY`.

This deliberately does not introduce compound-expression data-flow analysis.
source_b Algorithm 33 is correspondingly recorded as an expected static-semantic
failure because `result` is not structurally guaranteed to be assigned before
`RETURN result`; no initial value is invented.

See `docs/definite_assignment_control_flow_audit_v4_01_working.md`.

### Flow-sensitive dictionary GET resolution

Semantic resolution of `receiver.GET(...)` as the dictionary intrinsic now
follows current lexical/control-flow evidence. Reassignment to a non-dictionary
clears stale evidence, one-sided branch/loop evidence does not leak outward,
and nested functions inherit only unshadowed enclosing dictionary evidence.
Unknown receivers continue to retain ordinary user-defined `GET` semantics.

### Abrupt-flow alignment in semantic analysis

`BREAK` and `CONTINUE` are now treated as non-fallthrough for statements later
in the same loop body when computing definite assignment and dictionary receiver
evidence. Their loop-exit/next-iteration states are retained conservatively,
matching the compiler representation analysis. Named `CATCH` variables remain
catch-local even when the catch branch is the only path that reaches `ENDTRY`.

## Dialect impact

None. AJ dialect v1.1 and v1.2 source documents are unchanged.

- AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
- AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`

## Validation

1052 pytest passed, 3 skipped, 5 subtests passed; 332 unittest passed, 1 skipped.
