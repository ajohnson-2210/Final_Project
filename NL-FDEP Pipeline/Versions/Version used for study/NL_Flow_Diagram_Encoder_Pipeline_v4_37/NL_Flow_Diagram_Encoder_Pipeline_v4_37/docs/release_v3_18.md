# NL-FDEP v3.18 release record

## Scope

v3.18 implements the approved source_f Algorithm 41 structural wrapper recovery and the approved Python RANGE endpoint rendering cleanup. The frozen AJ_24038155 Dialect v1.1 grammar is unchanged.

## GC219 — evidenced input/helper/final-return wrapper

GC219 applies only to indentation-style generic pseudocode with one or more bare top-level `INPUT` declarations followed by one or more complete top-level helper routines and exactly one final top-level `RETURN`. The final return must call at least one supplied helper. Any unrelated top-level executable statement, input after a helper declaration, explicit canonical END declaration, class container, or final return that does not call a supplied helper prevents recovery.

Eligible source is wrapped in neutral `FUNCTION unnamed_function ACCEPTS(...)`. Bare input names become parameters; helper bodies and the final return are merely nested. No missing helper implementation is added.

For source_f Algorithm 41 this removes the top-level-RETURN structural failure while deliberately leaving `isSafe(board, row, col)` and `emptyBoard(N)` unresolved. The algorithm therefore remains an expected source-level failure for undefined essential routine dependencies.

## Python RANGE rendering — exact synthetic cancellation

Inclusive generic-source loops are canonicalised to AJ end-exclusive RANGE endpoints by adding one to the source upper bound. When that creates exactly `(X - 1) + 1`, the Python compiler now renders the stop expression as `X`. Thus source `FOR col FROM 0 TO N - 1` compiles as `for col in range(0, N):`.

This cleanup is restricted to `_compile_range_end_expression`; it is not a general arithmetic simplifier. Non-unit forms such as `(Limit - 2) + 1` remain structurally intact unless covered by the pre-existing LENGTH-derived endpoint rule.

AJ_24038155 Dialect v1.1 remains frozen and unchanged.
