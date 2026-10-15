# Corpus-wide nested stack push and explicit class canonicalisation — v2.96

## GC202 — balanced evidenced stack push

The long-standing GC037 rule converts simple Python-like stack pushes:

```text
stack.push(value)
```

into the existing AJ list-backed stack representation:

```text
APPEND value TO stack
```

GC037 intentionally uses a simple argument regex and therefore cannot see through nested calls. GC202 adds the balanced counterpart for expressions such as:

```text
destination.push(source.pop())
```

The receiver must have direct list/stack backing evidence in the same source (`EMPTY LIST`, list literal/list-value evidence, `AS LIST`, or the pre-existing `empty stack` surface that GC160 maps to `EMPTY LIST`). A method named `push` alone is not enough evidence.

GC202 preserves the nested argument; it does not invent `pop`, transfer logic or stack behaviour.

## GC203 — explicit legacy stateful class to frozen AJ class grammar

Some sources explicitly declare a `CLASS`, initialise instance-like state at class scope, and then provide `FUNCTION` operations over that state. Frozen AJ v1.1 expresses the same supplied structure using:

```text
PROPERTY
CONSTRUCTOR
METHOD
THIS
ENDCLASS
```

GC203 performs that representation mapping only when all of the following are true:

- the whole source is one explicit class;
- one or more plain self-contained state initialisers precede the methods;
- one or more complete `FUNCTION ... ENDFUNCTION` methods are present;
- every method references declared state;
- state names are not shadowed by method parameters;
- there are no free outer statements or external/unbound constructor initialisers;
- an `EMPTY LIST` state is not directly targeted by an indexed write.

The last boundary is deliberate. An indexed write into an initially empty abstract array/list may require invented growth/allocation semantics; v2.95 records that as an expected-failure boundary. GC203 must not make such a source executable merely by repairing its class syntax.

When eligible, GC203:

```text
CLASS Example
    values <- EMPTY LIST
    FUNCTION add ACCEPTS(item)
        APPEND item TO values
    ENDFUNCTION
```

becomes:

```text
CLASS Example
    PROPERTY values AS LIST

    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.values <- EMPTY LIST
    ENDCONSTRUCTOR

    METHOD add ACCEPTS(item)
        APPEND item TO THIS.values
    ENDMETHOD
ENDCLASS
```

An already supplied `ENDCLASS` is reused semantically rather than duplicated; a missing terminal `ENDCLASS` is added only inside an otherwise complete eligible class shape.

## Non-inference guarantees

- No model, filename, algorithm number or class/method name is inspected.
- No arbitrary object is inferred to be a list/stack from `.push(...)` alone.
- No external constructor parameter is invented.
- No array capacity, allocation, append-or-overwrite branch or pop-storage mutation is invented.
- AJ_24038155 Dialect v1.1 remains frozen and unchanged.
