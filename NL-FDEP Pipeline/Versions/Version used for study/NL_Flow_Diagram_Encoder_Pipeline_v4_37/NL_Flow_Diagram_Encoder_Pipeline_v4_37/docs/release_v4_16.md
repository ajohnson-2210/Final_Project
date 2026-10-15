# NL-FDEP v4.16 — source-neutral naming cleanup

## Status

AJ_24038155 Dialect remains **v1.4**. No parser, AST, flow, compiler, normalisation, scoring or behavioural semantics are changed by this release.

## Changes

- Removed historical AI-agent/vendor names from distributed filenames and text content.
- Replaced corpus-origin labels with anonymous `source_a`–`source_f` identifiers only where a stable regression-fixture distinction is necessary.
- Renamed reusable corpus adapters by input format rather than source identity:
  - `NumberedSectionAdapter`
  - `ExampleSectionAdapter`
  - `StructuredExportAdapter`
  - `TextExportAdapter`
- Renamed source-labelled normalisation helper functions to the behaviour they recognise, such as LRU-class, linear-search, bubble-sort and inventory-update recovery.
- Removed test caches from the distributable package.

## Neutrality rule

The pipeline does not select a semantic transformation because of a vendor or model identity. Compatibility handling is triggered by syntax, structural evidence, or a documented source pattern. Anonymous source identifiers in historical regression tests identify fixtures only and do not alter runtime processing policy.

## Validation

- 1,194 pytest tests passed
- 3 pytest tests skipped
- 5 subtests passed
- 344 unittest tests passed
- 1 unittest test skipped
