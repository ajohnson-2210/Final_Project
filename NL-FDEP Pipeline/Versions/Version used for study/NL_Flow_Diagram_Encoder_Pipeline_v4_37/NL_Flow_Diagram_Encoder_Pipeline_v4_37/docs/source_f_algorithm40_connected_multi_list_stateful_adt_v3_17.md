# source_f Algorithm 40 — connected multi-list stateful ADT recovery — v3.17

## Source evidence

The audited response explicitly initialises two persistent empty list states, `s1` and `s2`, then supplies two top-level operations. `enqueue` appends new values to `s1`. `dequeue` reads both lists and, when `s2` is empty, destructively transfers values from `s1` to `s2` before popping from `s2`.

The source therefore supplies all state initialisers, all queue operations, and the cross-state transfer that connects both lists into one persistent abstraction. The structural wrapper is omitted, but no queue algorithm is missing.

## GC218 recovery

GC218 is deliberately narrower than a generic `global lists + functions -> class` rule. It requires:

1. two to six top-level persistent assignments, all explicitly `EMPTY LIST`;
2. at least two complete top-level functions and no nested/free executable content;
3. every function to reference at least one evidenced state and no parameter to shadow state;
4. one connected bipartite graph containing every state and operation;
5. every state to be actively mutated by an existing list operation;
6. at least one explicit destructive cross-state transfer of the form `APPEND a.pop() TO b` with distinct evidenced state names;
7. no unknown `CALL` escape, direct state rebinding, or indexed state write.

When these conditions hold, GC218 emits neutral frozen-AJ class grammar with `LIST` properties, a zero-argument constructor that reuses only the source-supplied empty-list initialisers, and source-supplied functions represented as methods with `THIS`-qualified state references.

No semantic class name, queue sentinel, underflow policy, operation, or data value is invented.

## Empty dequeue boundary

The source ends `dequeue` with `s2.pop()` and does not supply an empty-queue guard or sentinel. v3.17 preserves that behaviour. It does not add `RETURN NONE`, `ERROR`, or another empty-queue policy. In generated Python, a dequeue from an empty recovered queue therefore retains the ordinary empty-list pop error.

## Behavioural validation

The recovered class was compared with a reference FIFO queue over random mixed enqueue/dequeue sequences. FIFO return order and represented queue state matched throughout. Existing source_f 37 counted-list recovery, the earlier explicit-class two-stack queue recovery, and all prior compatibility rules remain independently guarded.
