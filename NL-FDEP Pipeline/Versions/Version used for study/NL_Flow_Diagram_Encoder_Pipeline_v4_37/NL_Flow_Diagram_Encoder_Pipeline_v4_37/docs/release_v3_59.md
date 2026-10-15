# Release v3.59 — retire GC159 transaction-name flattened-property inference

## Scope

This release removes the transaction-name-based semantic inference from GC159 while leaving the separate GC146 inventory-update recogniser unchanged.

## Retired GC159 behaviour

A loop such as:

```text
FOR EACH transaction IN transactions DO
    OUTPUT transaction_quantity
ENDFOR
```

no longer causes `transaction_quantity` to become `transaction.quantity`. The same refusal applies to `transaction_itemID`, `transaction_item`, and `transaction_type`.

AJ v1.1 permits `_` inside identifiers. The names `transaction` and `transactions` do not independently establish that an underscored identifier denotes member access, so GC159 now preserves those spellings.

## Preserved behaviour

Explicit member access such as `transaction.itemID` or `transaction.quantity` is preserved. GC159's other specialised object-context recoveries are unchanged. GC146's separate `updateInventory(inventory, transactions)` recogniser is also unchanged and may still recover `transaction.item`, `transaction.type`, and `transaction.quantity` when all of its existing algorithm-specific evidence is present.

## Validation

- focused GC159/adjacent regression gate: 120 passed.
- in-tree pytest: 861 passed, 3 skipped, 5 subtests passed.
- in-tree unittest: 274 passed, 1 skipped.
- frozen dialect SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.
