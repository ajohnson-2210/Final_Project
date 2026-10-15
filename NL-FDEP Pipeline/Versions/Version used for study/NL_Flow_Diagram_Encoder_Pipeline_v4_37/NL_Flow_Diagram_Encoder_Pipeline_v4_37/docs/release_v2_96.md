# NL-FDEP v2.96 release record

## Scope

v2.96 implements the approved source_c Algorithm 40 recovery as two corpus-wide representation rules:

- GC202: balanced nested `push(...)` normalisation for explicitly list/stack-backed receivers;
- GC203: conservative canonicalisation of an explicit legacy stateful class into frozen AJ v1.1 `PROPERTY` / `CONSTRUCTOR` / `METHOD` / `THIS` syntax, including a missing terminal `ENDCLASS` only when the class is otherwise complete.

No queue algorithm, stack routine, class constructor dependency or storage-growth behaviour is invented.

## source_c 40 classification

```text
status: PASS AFTER CANONICAL AJ STACK-PUSH SURFACE NORMALISATION
        AND EXPLICIT STATEFUL CLASS CANONICALISATION
semantic inference: NO new algorithm semantics
algorithmic reconstruction: NO
dialect change: NO
```

## Regression evidence

- Exact source_c 40 occurrence parses, compiles and preserves FIFO behaviour.
- Generic nested `destination.push(source.pop())` normalises only with explicit stack/list backing evidence.
- An unrelated object `.push(...)` without collection evidence is not reclassified.
- Existing simple GC037 push behaviour remains unchanged.
- Generic explicit stateful classes canonicalise to frozen AJ class grammar with or without a supplied `ENDCLASS`.
- External/unbound class initialisers are not turned into invented constructor dependencies.
- Empty-list indexed-write class state remains outside GC203, preserving the v2.95 abstract-array expected-failure boundary.

## Validation

Working tree:

```text
pytest: 426 passed, 3 skipped, 5 subtests passed
unittest: 250 passed, 1 skipped
```

Fresh extraction of the packaged ZIP:

```text
pytest: 426 passed, 3 skipped, 5 subtests passed
unittest: 250 passed, 1 skipped
AJ v1.1 SHA-256: 0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598
```
