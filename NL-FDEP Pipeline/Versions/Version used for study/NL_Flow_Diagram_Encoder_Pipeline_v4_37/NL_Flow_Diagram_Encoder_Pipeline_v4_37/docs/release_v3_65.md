# Release v3.65 — retire GC159 specialised level-order flattened-property inference

## Scope

This release removes GC159's remaining specialised conversion of valid identifiers `node_value`, `node_left`, and `node_right` into `node.value`, `node.left`, and `node.right` inside the guarded `LEVEL_ORDER_TRAVERSAL(root)` context.

## Retired GC159 behaviour

Earlier releases had already removed the generic `root` + `node_*` inference but retained a narrower exception when the function was specifically `LEVEL_ORDER_TRAVERSAL(root)` and `node` was explicitly obtained from `DEQUEUE(queue)` (or the already-canonicalised `REMOVE FIRST ITEM FROM queue`). v3.65 retires that exception as well.

The queue/dequeue evidence establishes that `node` is the current traversal element. It does not establish that a separate valid identifier named `node_value`, `node_left`, or `node_right` denotes a property of that element. AJ_24038155 Dialect v1.1 permits underscores in identifiers and represents member access explicitly with `.`.

Therefore the following remain distinct:

- `node_value` — ordinary identifier;
- `node.value` — explicit member access;
- `node_left` — ordinary identifier;
- `node.left` — explicit member access;
- `node_right` — ordinary identifier;
- `node.right` — explicit member access.

## Preserved behaviour

Explicit source member access remains unchanged. A level-order source that actually says `OUTPUT node.value`, `APPEND node.left TO queue`, or `APPEND node.right TO queue` continues to parse and compile with those member accesses.

Historical flattened fixtures are no longer repaired into member access. If a flattened identifier is read in the parser's currently approved direct bare-read subset (for example `OUTPUT node_value`), the existing declaration-before-use check applies. The validator deliberately does not yet perform full compound-expression definite-assignment analysis, so flattened names used only in such unanalysed positions remain unresolved identifiers rather than being reinterpreted.

## Validation

- focused level-order/GC159 boundary gate: 13 passed;
- full pytest gate: 884 passed, 3 skipped, 5 subtests passed;
- full unittest gate: 297 passed, 1 skipped;
- frozen AJ_24038155 Dialect v1.1 SHA-256 unchanged: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

No parser, compiler, intrinsic, or frozen AJ_24038155 Dialect v1.1 semantics change in v3.65.
