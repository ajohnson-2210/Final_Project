# source_b Algorithm 41 — N-Queens expected-failure audit — v2.85

## Study occurrence

source_b Algorithm 41 supplies a concrete backtracking skeleton:

- initialise an `N x N` board of zeroes;
- call `placeQueens` from row 0;
- iterate candidate columns;
- place a queen with `board[row][col] <- 1`;
- recurse to the next row;
- backtrack with `board[row][col] <- 0`.

However, two essential operations are not executable definitions:

- `RECORD solution`
- `CHECK column, upper-left diagonal, upper-right diagonal for queens` followed by `RETURN True if no conflicts`

The source does not define solution storage/return semantics and does not implement the column or diagonal scans.

## Classification

**EXPECTED FAIL — MISSING NON-BUILT-IN ROUTINES / ALGORITHMIC DETAIL**

- structural recovery possible: partial
- structural recovery sufficient: no
- semantic inference required for complete execution: yes
- algorithmic reconstruction required: yes
- complete Python generation justified: no

## GC142 finding

Legacy rule `GC142` reconstructed a complete first-solution-returning N-Queens implementation from this incomplete description. It invented:

- the `isSafe` column/diagonal loops;
- `RETURN board` at the terminal row;
- recursive-result assignment and propagation;
- a null failure sentinel;
- return behaviour not supplied by the response.

This crossed the semantic-alignment boundary and could also encode incorrect endpoint behaviour. v2.85 removes the GC142 reconstruction path.

## v2.85 measure

The exact source_b occurrence is detected before generic literal/call recovery and is kept visibly non-executable. The compatibility layer does not create a replacement `isSafe` routine or solution-recording mechanism.

A second regression uses the historical canonical-ish shape that previously activated GC142 and verifies that it is no longer reconstructed.

A separately supplied, explicitly implemented `isSafe` routine remains allowed and parseable; the expected-failure guard therefore targets missing routine semantics rather than the N-Queens domain itself.

## General evidence rule

This audit adopts the v2.85 undefined-routine boundary: a missing routine may be preserved as recoverable only if it is a defined AJ/Python/runtime intrinsic, explicitly defined in the pseudocode, or explicitly imported. Domain knowledge alone is not sufficient evidence for implementation.
