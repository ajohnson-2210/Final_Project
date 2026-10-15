# Release v3.73 — GC160 parent-matrix dimension inference retired

## Problem

source_c Algorithm 49 contains two materially different matrix declarations:

```text
visited <- 2D boolean array same size as maze initialized to BOOLEAN(False)
parent <- 2D array to store previous cell for reconstruction
```

The first explicitly supplies both the dimension relationship and the initial value. The second supplies neither dimensions nor a fill value. GC160 nevertheless expanded the second declaration to:

```text
parent <- CALL create_matrix(LENGTH OF maze, LENGTH OF maze[0], CALL NULL())
```

That silently invented the parent matrix dimensions.

## Change

GC160 no longer expands the descriptive `parent` declaration. It remains visible as unresolved source and strict AJ parsing fails before Python generation. No matrix dimensions are inferred.

The explicit same-size declaration remains supported:

```text
visited <- 2D boolean array same size as maze initialized to BOOLEAN(False)
```

continues to canonicalise to:

```text
visited <- CALL create_matrix(LENGTH OF maze, LENGTH OF maze[0], BOOLEAN(False))
```

and compiles to a `len(maze) x len(maze[0])` boolean matrix.

source_c Algorithm 49 was already expected-fail because its maze-navigation predicates remain abstract, so this semantic-integrity correction does not change the aggregate corpus parse floor.

## Validation

- pytest: 906 passed, 3 skipped, 5 subtests passed
- unittest: 306 passed, 1 skipped
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
