# source_c Algorithm 47 audit — v2.97

## Motivating occurrence

```text
FUNCTION updateInventory(inventory, transactions):
    FOR each transaction in transactions:
        itemID = transaction.itemID
        quantityChange = transaction.quantity // positive for delivery, negative for purchase
        IF itemID IN inventory:
            inventory[itemID] = inventory[itemID] + quantityChange
        ELSE:
            // Handle new item, maybe set initial stock
            inventory[itemID] = quantityChange
    // Ensure no negative inventory (adjust accordingly)
    FOR each item in inventory:
        IF inventory[item] < 0:
            inventory[item] = 0 // or raise error
    RETURN inventory
```

## Classification

```text
status: PASS AFTER CASE-PRESERVING MEMBER-ACCESS COMPILATION
source algorithm: COMPLETE
semantic inference: NO
algorithmic reconstruction: NO
source logic correction: NO
compiler correctness fix: YES
dialect change: NO
```

## Defect

The normaliser correctly produced `transaction.itemID`, but the compiler changed it to `transaction.itemid`. Python attribute identifiers are case-sensitive, so this was not semantics-preserving.

## Correct result

Canonical AJ retains:

```text
itemID <- transaction.itemID
quantityChange <- transaction.quantity
```

Python now retains:

```python
itemID = transaction.itemID
quantityChange = transaction.quantity
```

The regression executes the generated Python against transaction objects that explicitly expose `itemID` and verifies inventory updates including the source-specified clamp of negative inventory to zero.
