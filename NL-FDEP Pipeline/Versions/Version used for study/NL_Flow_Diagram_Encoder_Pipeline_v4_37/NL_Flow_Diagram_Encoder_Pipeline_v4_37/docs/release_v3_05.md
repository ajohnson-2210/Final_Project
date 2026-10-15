# NL-FDEP v3.05 release record

## Scope

v3.05 implements the approved source_f corpus-adapter structure correction.

## Production change

`StructuredExportAdapter` now prefers the current structured `# <title>` corpus format when hash headings are present:

- hash headings delimit corpus tasks;
- task bodies retain original newlines and relative indentation;
- nested `INPUT`, `INIT`, and `FUNCTION` lines remain inside the current task;
- outer separator blank lines are removed without flattening the body;
- the legacy compressed-body extractor remains as a fallback for sources without hash headings.

No pseudocode normaliser, AJ parser, compiler, or dialect rule is changed.

## Motivating source_f occurrence

source_f Algorithm 7 (`Split Sentence into Words`) is stored as valid multiline, indented source. Pre-v3.05 extraction flattened that structure before normalisation. v3.05 preserves it exactly enough for the normalisation audit to consider the actual source representation.

## Audit boundary

- semantic inference: **NO**
- algorithmic reconstruction: **NO**
- source correction: **NO**
- corpus extraction correction: **YES**
- dialect change: **NO**

source_f Algorithm 7 still has a separate `char is space` representation issue. v3.05 does not change that pseudocode.

## Dialect

AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## Validation

Working tree:

- pytest: **500 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**

Fresh extraction from packaged ZIP:

- pytest: **500 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
