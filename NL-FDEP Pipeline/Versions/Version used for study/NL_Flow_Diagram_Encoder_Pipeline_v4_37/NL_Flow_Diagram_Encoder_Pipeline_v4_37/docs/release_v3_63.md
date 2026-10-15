# Release v3.63 — retire GC146 updateInventory flattened transaction-property inference

## Scope

This release removes GC146's conversion of valid AJ identifiers `transaction_item`, `transaction_type`, and `transaction_quantity` into `transaction.item`, `transaction.type`, and `transaction.quantity` merely because they occur in `FUNCTION updateInventory ACCEPTS(inventory, transactions)`.

AJ_24038155 Dialect v1.1 permits underscores in identifiers. The function name, parameter names, iterator spelling, and flattened identifier names do not independently establish object-member structure, so compatibility normalisation must not invent the dot access.

## Retired GC146 behaviour

For example:

```text
FUNCTION updateInventory ACCEPTS(inventory, transactions)
    transaction_item <- STRING("local")
    transaction_type <- STRING("audit")
    transaction_quantity <- 1
    FOR EACH transaction IN transactions DO
        OUTPUT transaction_item
        OUTPUT transaction_type
        OUTPUT transaction_quantity
    ENDFOR
    RETURN inventory
ENDFUNCTION
```

now preserves all three `transaction_*` identifiers exactly as written. It no longer rewrites them as members of `transaction`.

Explicit source member access such as `transaction.item`, `transaction.type`, and `transaction.quantity` remains unchanged.

## Preserved independent GC146 surface recovery

GC146's separate `ALERT expression` to `OUTPUT expression` surface normalisation remains available. The retirement is limited to the transaction-property inference.

Historical sources that read undeclared `transaction_item`/`transaction_type`/`transaction_quantity` now correctly reach declaration-before-use semantic failure instead of being silently repaired into object properties.

## Validation

- focused GC146/transaction-property boundary gate: 8 passed;
- full pytest gate: 876 passed, 3 skipped, 5 subtests passed;
- full unittest gate: 289 passed, 1 skipped;
- frozen dialect SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

No parser, compiler, intrinsic, or frozen AJ_24038155 Dialect v1.1 semantics change in v3.63.
