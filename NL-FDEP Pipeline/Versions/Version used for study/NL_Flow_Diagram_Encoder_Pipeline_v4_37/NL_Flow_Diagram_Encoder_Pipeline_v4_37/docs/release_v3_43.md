# NL-FDEP v3.43 release record

## Scope

v3.43 implements the approved source_d Algorithm 40 contextual `Stack()` representation recovery while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC244 contextual list-backed Stack() state recovery

Within an explicit class whose canonical constructor assigns a member from the exact zero-argument free constructor `Stack()`, GC244 may represent that state as `EMPTY LIST` when the same member is independently used as a stack in the class through source-supplied `push`, `pop`, or `isEmpty` behaviour.

For an evidenced member:

```text
self.stack_in <- Stack()
```

becomes:

```text
self.stack_in <- EMPTY LIST
```

Existing simple or nested pushes on that same evidenced state are represented with ordinary AJ `APPEND`, while the already-supported member `pop()` and `LENGTH OF ... == 0` representation from `isEmpty()` are preserved.

The rule is deliberately contextual and refuses local `Stack()` calls outside class state, non-zero-argument `Stack(...)`, members with no stack-use evidence, and members that are directly rebound after initialisation. No general object named `Stack`, arbitrary member method, queue policy, or new collection semantics are inferred.

source_d Algorithm 40 therefore compiles to two ordinary Python list-backed stacks and preserves its supplied queue-via-two-stacks FIFO behaviour.

## Validation

- targeted GC244 regression and refusal-boundary tests: 5 passed;
- full pytest suite: 767 passed, 3 skipped, 5 subtests passed;
- full unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 767 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
