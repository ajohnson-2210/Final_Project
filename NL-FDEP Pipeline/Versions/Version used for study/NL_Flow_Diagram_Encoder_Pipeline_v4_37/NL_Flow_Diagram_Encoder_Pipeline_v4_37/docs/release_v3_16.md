# NL-FDEP v3.16 release record

## Scope

v3.16 implements the approved recovery identified while auditing source_f Algorithm 37. It adds GC216 for a narrowly evidenced counted-list stateful ADT expressed as explicitly initialised outer state followed by multiple operations, and GC217 for an exact standalone `ERROR` statement.

## Production changes

### GC216 — evidenced counted-list stateful ADT

GC216 runs after ordinary compatibility and block recovery have exposed canonical assignments, functions, list operations and postfix updates. It is deliberately narrower than a generic `state + functions -> class` transformation.

The rule requires:

1. exactly two persistent state assignments before all operations;
2. exactly one state initialised as `EMPTY LIST` and the other as numeric zero;
3. at least three top-level functions after the state declarations;
4. every function to reference both state values, with no parameter shadowing either state name;
5. explicit list-operation evidence for `APPEND`, zero-argument member `pop()`, and indexed top access using `count - 1`;
6. explicit counter updates of `count <- count + 1` and `count <- count - 1`;
7. no direct list rebinding, indexed list write, nested function container or unknown free `CALL` escape.

When all conditions hold, the source is represented using frozen AJ class grammar with:

- neutral `CLASS unnamed_class`;
- typed list and integer properties;
- a zero-argument constructor using only the source-supplied initial values;
- source-supplied functions preserved as methods;
- shared-state references qualified through `THIS`.

No semantic class name or stack algorithm is invented.

### GC217 — standalone error signal

An exact executable statement `ERROR` is represented as:

```text
RAISE STRING("ERROR")
```

This is distinct from GC204. Existing `RETURN ERROR` continues to mean the returned string sentinel `"ERROR"`; assignments such as `status <- ERROR`, identifiers such as `ERROR_CODE`, and member names remain outside GC217.

## source_f Algorithm 37

The exact response supplies both persistent state values (`stack = []`, `size = 0`) and the complete `push`, `pop`, and `peek` behaviour. GC216 therefore recovers the structurally implied stateful ADT without supplying missing data or operations. The two empty-stack branches explicitly state `ERROR`, so GC217 preserves those branches as explicit AJ error generation.

Classification:

**PASS AFTER EVIDENCED STATEFUL-ADT STRUCTURAL RECOVERY — TRUSTWORTHY EXECUTABLE**.

## Dialect

AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## Validation

Working tree after the v3.16 change:

- pytest: **620 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`

Fresh extraction from packaged ZIP:

- pytest: **620 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
