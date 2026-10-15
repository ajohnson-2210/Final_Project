# source_f Algorithm 41 — omitted outer-wrapper recovery — v3.18

## Source evidence

The response supplies `INPUT N`, a complete recursive helper `placeQueen(row, board)`, and a final top-level `RETURN placeQueen(0, emptyBoard(N))`. That shape strongly evidences an omitted neutral algorithm container, but it does not supply implementations for `isSafe(...)` or `emptyBoard(...)`.

## Recovery boundary

GC219 wraps the input, helper, and final return in `FUNCTION unnamed_function ACCEPTS(N)`. It does not create a semantic function name and does not implement either missing dependency. The recursive helper remains source-named and source-shaped.

The inclusive source loop `FOR col from 0 to N-1` remains canonical AJ `IN RANGE 0 TO (N - 1) + 1`; the v3.18 Python range renderer collapses only that synthetic endpoint cancellation to `range(0, N)`.

## Audit classification

source_f Algorithm 41 remains **EXPECTED FAIL — ABSTRACT / UNDEFINED ROUTINE DEPENDENCIES** because `isSafe` and `emptyBoard` are essential and absent. The pipeline structural failure is fixed independently.
