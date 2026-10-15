# Release v3.60 — retire GC159 generic binary-tree flattened-property inference

## Scope

This release removes GC159's generic conversion of valid identifiers such as `node_value`, `node_left`, and `node_right` into `node.value`, `node.left`, and `node.right` merely because the source also contains an identifier named `root`.

## Retired GC159 behaviour

For example:

```text
FUNCTION inspect ACCEPTS(root)
    node_value <- 5
    OUTPUT node_value
    RETURN root
ENDFUNCTION
```

now preserves `node_value` exactly as written. The same refusal applies to `node_left` and `node_right`.

AJ v1.1 permits `_` inside identifiers. The presence of `root` does not independently establish that another identifier named `node_value`, `node_left`, or `node_right` denotes member access on an object named `node`.

Historical level-order-like fixtures whose only evidence was naming now preserve their underscored identifiers. If the preserved source is not valid AJ for some other reason, that failure remains visible rather than being repaired through an invented object model.

## Preserved specialised level-order recovery

The separately gated `FUNCTION LEVEL_ORDER_TRAVERSAL ACCEPTS(root)` recovery remains. It requires evidence that `node` is obtained from `DEQUEUE(queue)`; because queue canonicalisation occurs earlier in the pipeline, the gate now also recognises the equivalent canonical intermediate form `node <- REMOVE FIRST ITEM FROM queue`.

Under that specific context, the existing recoveries `node_value -> node.value`, `node_left -> node.left`, and `node_right -> node.right` remain available.

Explicit source member access such as `node.value` is unchanged.

## Validation

- focused GC159 binary-tree boundary gate: 9 passed.
- in-tree pytest: 866 passed, 3 skipped, 5 subtests passed.
- in-tree unittest: 279 passed, 1 skipped.
- frozen dialect SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.
