# Release v3.54 — source_e 37 class-state composition

## Scope

This release contains the two approved compatibility/compiler fixes exposed by source_e algorithm 37.

## GC241 canonical-class composition

GC241 now recognises an explicit class whose header has already been canonicalised from `CLASS Name` to `CLASS Name ACCEPTS(...)`.  It can therefore still recover direct-child `Constructor(...)` and `FUNCTION ...` declarations as frozen-AJ `CONSTRUCTOR` and `METHOD` blocks.  Existing refusal boundaries remain: the source must still be one explicit class with both constructor and method evidence and no trailing top-level material.

## Constructor-backed instance field inference

For canonical classes, the Python compiler now considers a direct unqualified identifier assignment in the constructor to be an instance-field candidate only when a canonical method subsequently references the same identifier without parameter shadowing.  Eligible names compile as `self.<name>` in both constructor and methods.

Safeguards:

- constructor-only temporaries remain locals;
- method parameters shadow inferred fields within that method;
- nested constructor assignments are not promoted by this rule;
- explicit `PROPERTY`/`THIS` class state remains unchanged;
- no array/list growth, allocation, or append semantics are inferred.

source_e 37 consequently advances from missing class-state binding to its independent source-level boundary: an empty Python list cannot satisfy `array[0] = element` without explicit growth/allocation semantics.

## Validation

- focused class/GC241 regression gate: 19 passed.
- in-tree pytest: 838 passed, 3 skipped, 5 subtests passed.
- in-tree unittest: 260 passed, 1 skipped.
- frozen dialect SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

Fresh-extraction rerun: 838 pytest passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped; frozen dialect hash unchanged.
