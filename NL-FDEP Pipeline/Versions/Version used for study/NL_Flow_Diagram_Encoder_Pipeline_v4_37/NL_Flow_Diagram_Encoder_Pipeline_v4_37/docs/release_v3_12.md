# NL-FDEP v3.12 release record

## Scope

v3.12 adds approved generic GC213 recovery for camelCase deque-style member operations on receivers that are independently evidenced as list-backed, and records source_f Algorithm 28 as an expected executable-correctness failure caused by a missing empty-deque guard in the source.

## Production change

`pseudocode_profiles.py` adds GC213 within the collection-operation normalisation stage.

Eligible source forms are:

```text
receiver.popFront()
receiver.popBack()
receiver.pushBack(value)
```

but only when `receiver` has direct list-backing evidence in the same source, such as:

```text
receiver = []
receiver <- EMPTY LIST
receiver AS LIST
```

The canonical mappings are:

```text
receiver.popFront()
    -> REMOVE FIRST ITEM FROM receiver

receiver.popBack()
    -> REMOVE LAST ITEM FROM receiver

receiver.pushBack(value)
    -> APPEND value TO receiver
```

`pushBack(...)` uses balanced argument scanning so nested call expressions are preserved without broadening the semantic rule.

GC213 does not globally reinterpret method names. A receiver without independent list-backing evidence retains ordinary AJ member-method semantics.

## source_f Algorithm 28

The exact source declares:

```text
result = []
deque = []
```

and therefore provides direct representation evidence for the three camelCase deque operations.

The source also contains:

```text
IF deque[0] == i - k:
```

before any item has been inserted into `deque`. v3.12 deliberately leaves that condition unchanged. Executing the faithfully recovered program therefore raises `IndexError: list index out of range` on the first iteration for a non-empty input array.

Classification:

**EXPECTED EXECUTABLE-CORRECTNESS FAILURE — SOURCE EMPTY-DEQUE GUARD NOT SUPPLIED**.

A regression control that adds the guard explicitly in the source demonstrates that GC213 removes the previously latent `popFront`/`popBack`/`pushBack` compatibility gap and the algorithm then produces the expected sliding-window maxima.

## Dialect

AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## Validation

Working tree after the v3.12 change:

- pytest: **580 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**

Fresh extraction from packaged ZIP:

- pytest: **580 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
