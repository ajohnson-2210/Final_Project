# Release v3.53 — source_a/source_e standing corpus integration

## Scope

This release adds the user-supplied source_a and source_e 50-algorithm response exports to the permanent regression corpus.  The source files are retained byte-for-byte under `tests/corpora/`.

## Non-lossy corpus loading

`corpus_evaluator.read_corpus_text()` now attempts UTF-8-SIG first and falls back to Windows-1252 only when UTF-8 decoding fails.  The previous `errors="replace"` path could silently replace valid Windows-1252 source characters such as `×` with U+FFFD.

## Permanent checks

`tests/test_source_a_source_e_corpus_regression_v3_53.py` verifies:

- exactly 50 source_a tasks are extracted by `NumberedSectionAdapter`;
- exactly 50 source_e tasks are extracted by `ExampleSectionAdapter`;
- source_e `Example:` sections are not included in executable pseudocode bodies;
- source_a source characters are preserved losslessly;
- all 100 items run through the normal compatibility/parser evaluation path;
- parse coverage does not regress below the integration baseline (source_a 38/50, source_e 45/50).

The parse floors are deliberately monotonic: future evidence-backed compatibility improvements may increase coverage without requiring snapshot rewrites.

## Semantic impact

None.  No pseudocode normaliser, AJ parser, Python compiler, intrinsic mapping, or frozen AJ_24038155 Dialect v1.1 semantics are changed.

## Validation

- in-tree pytest: 829 passed, 3 skipped, 5 subtests passed.
- in-tree unittest: 260 passed, 1 skipped.
- fresh-extraction rerun: 829 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
- frozen dialect SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

