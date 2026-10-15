# source_b Algorithm 49 — expected-failure audit — v2.87

## Source classification

source_b Algorithm 49 supplies a recognisable BFS skeleton: queue/path state, visited tracking, goal testing, enqueueing, and a no-path result.

However, it describes neighbour generation and branch-driving maze predicates rather than defining them:

```text
FOR each neighbour OF current (up/down/left/right)
IF neighbour is valid AND not a wall AND not visited THEN
```

## Missing executable semantics

The source does not define or import:

- the representation of `current`;
- how `up/down/left/right` produces neighbour values;
- the maze dimensions/bounds rule;
- the wall representation;
- a validity routine;
- a traversability routine.

Therefore a complete executable result would require algorithmic/environmental inference.

## v2.86 latent false pass

Historical GC147 could select tuple coordinates, generate four orthogonal neighbours, add explicit bounds arithmetic, and invent `is_traversable(maze, neighbour)`. That was a reconstruction of a conventional maze solution, not a recovery of supplied pseudocode semantics.

The exact raw source_b response happened to fail earlier on other compatibility mismatches, but GC147 remained a latent false-pass path for a slightly more normalised equivalent source.

## v2.87 result

Status:

```text
EXPECTED FAIL — MISSING NEIGHBOUR / TRAVERSABILITY SEMANTICS
```

v2.87 preserves the unresolved descriptive operations and requires strict parsing to fail rather than generating a conventional implementation.

No complete Python output is considered valid for the source as supplied.

## Regression evidence

`tests/test_source_b_algorithm49_expected_failure_v2_87.py` preserves the motivating source_b occurrence and verifies that v2.87 does not invent:

- coordinate tuples;
- row/column bounds logic;
- `is_traversable`;
- GC147 reconstruction.

`tests/test_abstract_maze_navigation_boundary_v2_87.py` and `tests/test_corpus_maze_navigation_boundary_v2_87.py` prove that the implementation is corpus-wide and source-shape independent.

## Dialect status

AJ_24038155 Dialect v1.1 remains frozen and unchanged.
