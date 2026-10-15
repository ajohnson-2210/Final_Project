# NL-FDEP v3.38 release record

## Scope

v3.38 implements the approved evidenced deque surface-operation recovery for source_d Algorithm 28 while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC237 evidenced deque surface-operation recovery

After v3.37 detaches inline `//` comments early, a declaration such as:

```text
deque = empty DoubleEndedQueue // Stores indices
```

is cleanly exposed as explicit deque backing before collection canonicalisation. GC237 uses that local source evidence to lower only the following standalone operations on the same receiver:

```text
REMOVE FRONT FROM deque
-> REMOVE FIRST ITEM FROM deque

REMOVE BACK FROM deque
-> REMOVE LAST ITEM FROM deque

ADD BACK value TO deque
-> APPEND value TO deque
```

The equivalent intermediate spelling `APPEND BACK value TO deque` is accepted because an earlier generic spelling pass may already have rewritten `ADD` to `APPEND`.

Evidence is lexical-routine local and is invalidated by direct reassignment. Unproven receivers and cross-routine reuse are not rewritten. The recovered operations map only to existing AJ v1.1 list primitives; no deque parser feature or dialect syntax is added.

source_d Algorithm 28 now preserves its explicit double-ended-queue operations and executes the standard sliding-window maximum behaviour correctly.

## Validation

- targeted GC237 regression/boundary tests: 5 passed;
- full pytest suite: 745 passed, 3 skipped, 5 subtests passed;
- unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 745 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
