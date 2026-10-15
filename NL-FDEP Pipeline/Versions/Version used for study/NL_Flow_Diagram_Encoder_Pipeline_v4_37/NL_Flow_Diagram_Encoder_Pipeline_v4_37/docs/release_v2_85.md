# NL-FDEP v2.85 release record

## Scope

v2.85 is a semantic-integrity correction driven by the source_b Algorithm 41 audit. It does not add parsing coverage for N-Queens. Instead, it removes an over-permissive legacy recovery that fabricated missing algorithmic behaviour.

## Changes

- Removed legacy `GC142` source_b-specific N-Queens reconstruction.
- Added an early expected-failure boundary for the source_b Algorithm 41 shape so undefined `RECORD solution` and `isSafe` semantics remain visible.
- Added regressions proving that both the exact study occurrence and the historical GC142 trigger shape are not reconstructed.
- Added a positive boundary regression confirming that an explicitly implemented N-Queens safety routine remains accepted.
- Documented the general undefined-routine recovery boundary: undefined/unimported non-built-in routines are not implemented from domain knowledge.

## Active dialect

AJ_24038155 Dialect v1.1 remains the active dialect. No dialect syntax change is introduced in v2.85.
