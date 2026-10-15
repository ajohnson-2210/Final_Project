# NL-FDEP v3.17 release record

## Scope

v3.17 implements the approved structural recovery identified while auditing source_f Algorithm 40. It adds GC218 for multiple explicitly initialised persistent list states whose source-local operations prove that the lists form one connected stateful abstraction.

## GC218 — evidenced connected multi-list stateful ADT

The rule runs after existing block, class, ordered-cache and counted-list recoveries. It activates only when all persistent outer state assignments are explicit `EMPTY LIST` values, multiple complete top-level functions follow, the state/function graph is connected, every list is actively mutated, and at least one operation explicitly transfers an item destructively from one evidenced list state to another.

The cross-state transfer requirement prevents GC218 from absorbing unrelated module-level list utilities. Additional refusals cover parameter shadowing, unknown helper-call escape, direct persistent-list rebinding, indexed writes, nested functions, free executable statements and disconnected state/operation groups.

Eligible source becomes neutral `CLASS unnamed_class` with source-supplied LIST properties and a zero-argument constructor. The original functions become methods and persistent state references are qualified with `THIS`. No semantic class name or algorithmic queue behaviour is added.

## source_f Algorithm 40 result

The exact response supplies `s1 = []`, `s2 = []`, `enqueue(x)`, the conditional two-stack transfer, and `dequeue()`. v3.17 recovers only the omitted stateful wrapper. Empty dequeue remains a source-preserved list-pop underflow because the source supplies no sentinel or explicit error branch.

AJ_24038155 Dialect v1.1 remains frozen and unchanged.
