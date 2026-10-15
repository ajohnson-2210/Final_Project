# NL-FDEP v2.86 release record

## Scope

v2.86 is a semantic-integrity correction driven by the source_b Algorithm 48 audit. It removes a false-pass route in which descriptive environmental file/folder predicates could be renamed to undefined helper calls.

## Changes

- Replaced the source_a Algorithm 48 shape-specific file/folder guard with a model- and algorithm-independent environmental predicate dependency guard.
- Prevented descriptive `X is a file/folder/directory` forms from becoming invented `is_file` / `is_directory` calls when the exact helper dependency is neither defined nor explicitly imported.
- Added the exact source_b Algorithm 48 study occurrence as versioned regression evidence.
- Added source-shape-independent negative coverage.
- Added corpus-wide regression shapes derived independently from source_a, source_b, source_e, and source_c occurrences, all exercising the same single predicate-level guard.
- Added unrelated synthetic names/wrappers to prove the rule does not depend on a corpus filename, model label, algorithm number, or function name.
- Added positive coverage proving explicitly defined exact helpers still permit the historical conversion.
- Added v1.1 member-call coverage proving `entry.is_file()` / `entry.is_directory()` remain unaffected.
- Added import-evidence and partial-import boundary tests.
- Recorded source_b Algorithm 48 as `EXPECTED FAIL — MISSING IMPORT / DEFINITION FOR ENVIRONMENTAL FILE-TYPE PREDICATES`.

## Active dialect

AJ_24038155 Dialect v1.1 remains frozen and unchanged. v2.86 introduces no dialect syntax or semantic revision.

## Validation

Working-tree validation after the corpus-wide generalisation:

- pytest: 333 passed, 3 skipped, 5 subtests passed;
- unittest: 242 passed, 1 skipped.
