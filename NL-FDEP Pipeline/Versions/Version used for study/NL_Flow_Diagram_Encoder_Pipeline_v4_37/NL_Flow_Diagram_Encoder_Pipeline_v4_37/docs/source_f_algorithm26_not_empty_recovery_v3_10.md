# source_f Algorithm 26 — Binary Tree Level-Order Traversal

## Motivating occurrence

The preserved source_f corpus contains:

```text
INPUT root

IF root == null:
    RETURN []

queue = [root]
result = []

WHILE queue not empty:
    levelSize = length(queue)
    currentLevel = []

    FOR _ from 0 to levelSize-1:
        node = queue.pop(0)
        currentLevel.append(node.value)

        IF node.left:
            queue.append(node.left)

        IF node.right:
            queue.append(node.right)

    result.append(currentLevel)

RETURN result
```

The only new compatibility surface required is `queue not empty`.

## Approved recovery

```text
queue not empty
```

becomes:

```text
LENGTH OF queue > 0
```

through generic GC211. The implementation does not inspect source_f, the algorithm number, `queue`, `root`, or tree member names.

## Canonical AJ result

The relevant loop becomes:

```text
WHILE LENGTH OF queue > 0 DO
```

The remaining list, queue-operation, member-access, and range forms reuse existing compatibility rules.

## Python result

The corresponding Python condition is:

```python
while len(queue) > 0:
```

No tree class is invented; the supplied `root` input is used exactly through the explicitly referenced `.value`, `.left`, and `.right` members.

## Audit classification

```text
status:
    PASS AFTER CONSERVATIVE OMITTED-IS EMPTY-PREDICATE RECOVERY

semantic inference:
    NO

algorithmic reconstruction:
    NO

control-flow correction:
    NO

tree implementation invented:
    NO

dialect change:
    NO
```
