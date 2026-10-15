# GC211 — omitted-`IS` non-empty predicate recovery

## Approved surface

Some corpus pseudocode writes the direct empty-state predicate without the optional copula:

```text
collection NOT EMPTY
```

GC211 treats that as the same predicate already supported by the compatibility layer:

```text
collection IS NOT EMPTY
```

and canonicalises the omitted-`IS` form to:

```text
LENGTH OF collection > 0
```

## Boundary

GC211 is deliberately limited to a simple identifier followed by the exact words `NOT EMPTY`, case-insensitively.

It does not reinterpret:

- `NOT BLANK`, `NOT NULL`, `NOT WHITESPACE`, or `NOT MISSING`;
- member expressions such as `state.queue NOT EMPTY`;
- longer identifiers such as `queue_not_empty`;
- text inside quoted strings;
- comments.

The pre-existing `identifier IS NOT EMPTY` path remains unchanged and is not relabelled as GC211.

## Semantic classification

This is syntax-surface recovery only. The source already states the non-empty condition, so no collection contents, algorithm steps, helper routines, or storage representation are invented.

- semantic inference: **NO**
- algorithmic reconstruction: **NO**
- dialect change: **NO**
