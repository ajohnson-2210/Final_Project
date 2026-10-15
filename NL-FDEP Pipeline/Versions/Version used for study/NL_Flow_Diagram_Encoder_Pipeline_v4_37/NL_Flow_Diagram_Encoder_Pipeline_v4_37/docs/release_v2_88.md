# NL-FDEP v2.88 release record

## Scope

v2.88 is a semantic-integrity correction driven by the source_b Algorithm 50 drone-coordination audit and cross-corpus review of the same coordination/collision-avoidance semantic family.

## Changes

- Replaced the old source_a-shape-specific Algorithm 50 guard with one corpus-wide abstract coordination/control semantic boundary.
- The implementation no longer depends on model name, filename, algorithm number, wrapper function, or corpus-specific variable names.
- Descriptive completion, proximity, environmental bounds, collision-risk and synchronisation statements remain unresolved rather than being operationalised.
- Python-like free coordination helpers that require compatibility conversion are blocked when the exact dependency is neither defined nor explicitly imported and is not a recognised AJ/Python intrinsic.
- Explicit AJ v1.1 member calls remain valid source-supplied interfaces.
- Added exact source_b Algorithm 50 expected-failure regression evidence.
- Added cross-source evidence for source_a, source_b, source_e, source_f, source_c and source_d surface forms, all exercising the same implementation rule.
- Added positive controls for locally defined helpers, explicitly imported helpers, explicit v1.1 member interfaces, and unrelated member-call algorithms.

## Audit classification

source_b Algorithm 50:

```text
EXPECTED FAIL — ABSTRACT CONTROL PREDICATES / MISSING COORDINATION DEPENDENCIES
```

The compatibility layer may preserve explicit structural and object-interface content but must not incorporate a conventional collision-avoidance/coordination solution for abstracted or unbound semantics.

## Active dialect

AJ_24038155 Dialect v1.1 remains frozen and unchanged. No dialect syntax or semantic revision is introduced by v2.88.

## Validation

Working-tree validation after the corpus-wide coordination correction:

- pytest: 360 passed, 3 skipped, 5 subtests passed;
- unittest: 242 passed, 1 skipped.

Extracted v2.88 package validation reproduced the same results:

- pytest: 360 passed, 3 skipped, 5 subtests passed;
- unittest: 242 passed, 1 skipped.
