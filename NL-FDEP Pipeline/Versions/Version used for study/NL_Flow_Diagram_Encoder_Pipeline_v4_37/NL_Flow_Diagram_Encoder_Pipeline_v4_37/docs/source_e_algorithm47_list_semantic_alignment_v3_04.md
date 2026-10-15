# source_e Algorithm 47 semantic-alignment audit — v3.04

## Motivating study occurrence

```text
FUNCTION UPDATE_INVENTORY(purchases, deliveries)
  inventory = []
  FOR item IN purchases
    IF item IN inventory THEN
      inventory[item] -= purchases[item]
    ELSE
      inventory[item] = -purchases[item]
    END IF
  END FOR
  FOR item IN deliveries
    IF item IN inventory THEN
      inventory[item] += deliveries[item]
    ELSE
      inventory[item] = deliveries[item]
    END IF
  END FOR
  RETURN inventory
END FUNCTION
```

The supplied example uses dictionary inputs and expects a dictionary-shaped result, but the algorithm itself explicitly initialises `inventory = []`.

## Boundary decision

`[]` is explicit source evidence for an empty list. The pipeline therefore preserves it as:

```text
inventory <- EMPTY LIST
```

and Python:

```python
inventory = []
```

Later keyed access such as `inventory[item]` does not authorise the pipeline to reinterpret that explicit list as a dictionary. Doing so would correct the source rather than preserve it.

The resulting Python can fail when non-integer keys are used. That failure is evidence of the source's internally inconsistent collection semantics, not a reason to invent a different collection representation.

## Classification

```text
Algorithm: source_e 47 — Inventory Update
status: EXPECTED FAIL — SOURCE COLLECTION SEMANTICS ARE INTERNALLY INCONSISTENT
source declaration: [] explicitly denotes EMPTY LIST
later source operations: keyed mapping-style access
example inputs/result: dictionary-shaped
pipeline representation: preserve EMPTY LIST / []
infer dictionary: NO
semantic alignment: PRESERVED
source correction required for successful example execution: YES
automatic source correction permitted: NO
algorithmic reconstruction: NO
dialect change: NO
```

No production normaliser/parser/compiler rule is added for this case.

AJ_24038155 Dialect v1.1 remains frozen and unchanged.
