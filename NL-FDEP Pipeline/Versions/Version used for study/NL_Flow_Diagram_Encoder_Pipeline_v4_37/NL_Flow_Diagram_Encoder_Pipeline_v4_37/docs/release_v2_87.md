# NL-FDEP v2.87 release record

## Scope

v2.87 is a semantic-integrity correction driven by the source_b Algorithm 49 maze-pathfinding audit and cross-corpus review of the same semantic family.

## Changes

- Removed the executable GC128 maze reconstruction path that assumed `Maze[Current]`, an adjacency-list graph representation, random graph inputs, and a generated wrapper.
- Removed the executable GC147 source_b maze reconstruction path that selected coordinate tuples, generated orthogonal neighbours, added bounds checks, and invented `is_traversable`.
- Removed the generic descriptive `within bounds` / `is not blocked` to explicit bounds plus `is_traversable` conversion.
- Added one corpus-wide unresolved maze/navigation semantic boundary.
- Added detection of undefined free navigation helpers such as `GetValidNeighbors(...)` when the exact helper is neither defined nor explicitly imported.
- Preserved explicit AJ v1.1 member interfaces such as `maze.getValidNeighbors(...)` and `maze.isTraversable(...)`.
- Added exact source_b Algorithm 49 expected-failure regression evidence.
- Added cross-source evidence covering distinct Algorithm 49 forms from source_a, source_b, source_c, source_e, source_d, and source_f, all exercising the same implementation rule.
- Added unrelated synthetic positive/negative tests so the rule cannot regress into model/file/algorithm-specific logic.

## Audit classification

source_b Algorithm 49:

```text
EXPECTED FAIL — MISSING NEIGHBOUR / TRAVERSABILITY SEMANTICS
```

The compatibility layer may preserve explicit BFS structure but must not incorporate a conventional maze solution for abstract or undefined neighbour, bounds, wall, validity, or traversability semantics.

## Active dialect

AJ_24038155 Dialect v1.1 remains frozen and unchanged. No dialect syntax or semantic revision is introduced by v2.87.

## Validation

Working-tree pytest validation after the corpus-wide correction:

- pytest: 347 passed, 3 skipped, 5 subtests passed.

- unittest: 242 passed, 1 skipped.

Extracted v2.87 package validation reproduced the same results:

- pytest: 347 passed, 3 skipped, 5 subtests passed;
- unittest: 242 passed, 1 skipped.
