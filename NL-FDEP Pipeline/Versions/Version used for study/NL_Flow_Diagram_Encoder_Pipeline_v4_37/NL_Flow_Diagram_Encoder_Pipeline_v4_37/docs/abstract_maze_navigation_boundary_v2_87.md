# Abstract maze/navigation semantic boundary — v2.87

## Rule

A compatibility normaliser must not turn descriptive maze/grid navigation semantics into an executable solution merely because a conventional implementation is familiar.

The boundary is corpus-wide and source-shape independent. It does not inspect model names, filenames, algorithm numbers, prompt labels, wrapper names, or function names.

## Unresolved descriptive forms

Examples include:

```text
FOR EACH neighbour OF current
FOR EACH neighbour OF current (up/down/left/right)
neighbour is valid
not a wall
cell is not blocked
row, col are within bounds
```

These phrases do not establish the concrete coordinate, graph, cell, wall, bounds, or adjacency representation required for execution.

## Undefined free navigation helpers

A free helper such as:

```text
GetValidNeighbors(maze, current)
is_traversable(maze, neighbour)
```

is also an unresolved dependency when the supplied pseudocode neither defines nor explicitly imports that exact helper.

An explicit object interface such as:

```text
maze.getValidNeighbors(current)
maze.isTraversable(neighbour)
```

is different: AJ_24038155 Dialect v1.1 already represents it as an explicit member call, so the compatibility layer does not invent a missing routine name or object binding.

## Historical false-pass paths removed

### GC128

GC128 previously interpreted `Neighbour of Current` as `Maze[Current]`, created a `find_path` wrapper, generated random graph inputs, and selected an adjacency-list representation absent from the source.

v2.87 removes that recovery path.

### GC147

GC147 previously interpreted source_b's `up/down/left/right` description as coordinate tuples, added row/column bounds checks, and invented an `is_traversable` helper.

v2.87 removes that recovery path.

### Generic blocked-cell conversion

A generic compatibility substitution previously changed descriptive text such as:

```text
newRow, newCol are within bounds
AND maze[newRow][newCol] is not blocked
```

into explicit bounds arithmetic plus `CALL is_traversable(...)`.

v2.87 removes that substitution. The descriptive source remains unresolved unless executable semantics are supplied.

## Accepted evidence

Recovery is allowed when the source itself supplies executable semantics, for example:

```text
FUNCTION GetValidNeighbors ACCEPTS(maze, current)
    ...
ENDFUNCTION
```

followed by an explicit call, or an explicit member interface such as:

```text
maze.getValidNeighbors(current)
```

An explicit import/binding of the exact free helper is also valid dependency evidence. The compatibility layer still must not invent the helper body or select a representation not supplied by that dependency.

## Empirical corpus evidence

Algorithm 49 outputs in the study corpus express the same semantic gap through different surface forms:

- source_a: `FOR EACH Neighbour of Current`;
- source_b: `FOR each neighbour OF current (up/down/left/right)` plus `neighbour is valid AND not a wall`;
- source_c: descriptive `within bounds` and `is not blocked` predicates;
- source_e: `cell IS NOT A WALL` without an executable wall predicate;
- source_d: free `GetValidNeighbors(maze, curr)` with no supplied definition/import;
- source_f: free `getValidNeighbors(curr, maze)` with no supplied definition/import.

These are regression evidence for one shared rule, not six model-specific rules.

## Dialect status

AJ_24038155 Dialect v1.1 remains frozen and unchanged. v2.87 is a compatibility-pipeline semantic-integrity correction only.
