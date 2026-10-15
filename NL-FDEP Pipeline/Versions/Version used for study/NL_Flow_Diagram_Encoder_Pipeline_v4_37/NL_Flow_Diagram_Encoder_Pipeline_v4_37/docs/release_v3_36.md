# NL-FDEP v3.36 release record

## Scope

v3.36 implements the approved source_d Algorithm 26 post-expansion queue-operation composition fix while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC235 post-expansion evidenced queue operations

source_d Algorithm 26 explicitly initialises `queue = empty Queue`, enqueues the root, dequeues each current node, and conditionally enqueues `node.left` and `node.right`. Earlier collection normalisation already represents the queue as a list-backed collection and lowers queue operations that are standalone at that point. The two child enqueue operations, however, are embedded in one-line `IF ... THEN ENQUEUE ...` statements until GC132 expands those conditionals later.

GC235 runs after final structural expansion and reuses only explicit local list-backing evidence. It maps a newly standalone evidenced operation such as:

```text
ENQUEUE node.left TO queue
```

to the existing frozen-AJ list operation:

```text
APPEND node.left TO queue
```

The equivalent free-call form and assignment-form dequeue counterpart are accepted under the same evidence guard. Evidence is lexical-routine local, and a direct reassignment invalidates it. Unproven receivers and cross-routine evidence are refused. No queue algorithm, branch, null policy, or collection type is invented.

## source_d Algorithm 26 result

The supplied level-order traversal now canonicalises, parses, encodes to a flow diagram, compiles deterministically, and executes with its supplied breadth-first semantics. Representative coverage includes a multi-level irregular binary tree and a null root.

## Validation

- targeted source_d 26 / GC235 regression and refusal-boundary tests: 4 passed;
- full pytest suite: 737 passed, 3 skipped, 5 subtests passed;
- unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 737 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
