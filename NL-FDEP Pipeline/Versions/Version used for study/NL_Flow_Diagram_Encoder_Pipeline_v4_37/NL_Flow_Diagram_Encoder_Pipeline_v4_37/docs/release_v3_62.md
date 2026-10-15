# Release v3.62 — retire GC159 generic maze-coordinate identifier inference

## Scope

This release removes GC159's conversion of valid underscored identifiers such as `start_row`, `start_col`, `current_row`, `current_col`, `direction_row`, and `direction_col` into indexed coordinate access merely because a function accepts `(maze, start, end)` and declares `directions`.

## Retired GC159 behaviour

For example:

```text
FUNCTION inspect ACCEPTS(maze, start, end)
    directions <- EMPTY LIST
    start_row <- 5
    OUTPUT start_row
    RETURN start
ENDFUNCTION
```

now preserves `start_row` exactly as written. It is no longer rewritten to `start[0]`.

AJ v1.1 permits `_` inside identifiers. The names `maze`, `start`, `end`, and `directions` do not independently establish a coordinate representation, so flattened row/column spellings are not sufficient evidence for list/tuple indexing.

Explicit source indexing such as `start[0]` remains unchanged.

## Preserved independent maze surface recovery

The existing explicit four-direction literal recovery remains available:

```text
directions <- [(0,1), (1,0), (0,-1), (-1,0)]
```

may still canonicalise to the existing `list_value(TUPLE(...))` form. Likewise, indexed assignments written with `=` may still canonicalise to `<-` inside the same narrowly recognised maze surface. These rules are independent of flattened coordinate names.

No bounds, wall, coordinate-shape, or traversal semantics are invented.

## Validation

- focused GC159 maze-coordinate boundary gate: 4 passed;
- GC159 maze-coordinate plus existing generic-obvious-mismatches gate: 114 passed;
- full pytest gate: 873 passed, 3 skipped, 5 subtests passed;
- full unittest gate: 286 passed, 1 skipped;
- frozen dialect SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

No parser, compiler, intrinsic, or frozen AJ_24038155 Dialect v1.1 semantics change in v3.62.
