# Release v3.56 — retire synthetic random input inference

## Scope

This release removes two obsolete compatibility behaviours that fabricated random input data solely to make early test scenarios executable.

## Retired GC119 behaviour

The recognised two-list intersection idiom no longer rewrites external list inputs to `CALL random_list()`. `INPUT List1` and `INPUT List2` remain external inputs.

## Retired synthetic-input portion of GC118

Matrix input plus an `N` dimension is no longer rewritten by deleting the matrix input and generating `CALL random_matrix(N, N)`. External matrix input is preserved.

GC118's independent transpose surface spelling remains available; this release does not remove transpose canonicalisation.

## Boundary

The compiler's `random_list` / `random_matrix` intrinsics are not removed. Explicit canonical AJ may still invoke them. v3.56 only prevents compatibility normalisation from inventing those calls when the source supplied external inputs.

## Validation

- focused retirement regression gate: 4 passed.
- in-tree pytest: 851 passed, 3 skipped, 5 subtests passed.
- in-tree unittest: 264 passed, 1 skipped.
- frozen dialect SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

Fresh-extraction rerun: 851 pytest passed, 3 skipped, 5 subtests passed; 264 unittest passed, 1 skipped; frozen dialect hash unchanged.
