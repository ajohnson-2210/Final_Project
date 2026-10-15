# Definite-assignment control-flow audit — post-v4.01 working tree

## Decision

AJ v1.2 requires an identifier to be declared or assigned before it is read. The static validator therefore now keeps a bare identifier introduced by control flow only when that identifier is definitely assigned on every structurally possible path reaching the read.

This remains deliberately limited to the validator's existing direct/bare-read subset. Compound-expression definite-assignment analysis is not introduced.

## Control-flow joins

- `IF / ELSE IF / ELSE`: a new binding survives the join only when every branch assigns it. If there is no final `ELSE`, the no-branch path is included.
- `WHILE`, `FOR`, and `FOR EACH`: names introduced only in the body do not escape, because the loop may execute zero times. Existing bindings remain visible.
- `TRY / CATCH`: a new binding survives `ENDTRY` only when both normal and caught-error paths establish it. A named `CATCH` error binding does not escape the catch body.

The existing implementation policy that loop variables themselves belong to the containing scope is unchanged; this audit concerns names introduced only by the loop body.

## Consequences for historical regression cases

Two synthetic deque compatibility tests previously returned a variable assigned only inside an `IF` without `ELSE`. They now correctly fail static semantic analysis rather than relying on value reasoning that the validator does not perform.

source_b Algorithm 33 (integer square root) previously passed because `result <- mid` occurs textually before `RETURN result`. Under definite assignment, `result` is not structurally guaranteed to be assigned after the loop: the validator does not infer numeric invariants proving that the loop executes and either returns or reaches the assigning branch. The pipeline must not repair this by inventing an initial value for `result`, so the occurrence is now an expected static-semantic failure.

This is intentionally conservative. A source that wants guaranteed acceptance can explicitly initialise `result` before the loop.

## Packaging

This is a static-semantic validator change only, not a Python compiler change. Under the study versioning rule it does not create a new packaged release. v4.01 remains the current package until a compiler change is warranted.
