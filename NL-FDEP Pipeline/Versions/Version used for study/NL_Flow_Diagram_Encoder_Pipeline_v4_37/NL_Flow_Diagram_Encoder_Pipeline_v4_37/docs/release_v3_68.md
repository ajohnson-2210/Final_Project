# Release v3.68 — GC161 makes recovered capacity state explicit and consistent

v3.68 closes a pseudocode/Python visibility mismatch in the recovered source_c `LRUCache` class.

## Change

When GC161 recognises source state of the form:

```text
capacity <- GIVEN CAPACITY
```

and recovers the legacy compatibility class header:

```text
CLASS LRUCache ACCEPTS(capacity)
```

it now makes the stored state explicit in canonical pseudocode:

```text
given_capacity <- capacity
```

The legacy Python compiler therefore emits the visible counterpart exactly once:

```python
self.given_capacity = capacity
```

rather than silently manufacturing `self.capacity = capacity` from the class parameter.

Once `given_capacity` has been declared as the recovered instance state, executable references to the original class-state name `capacity` inside the preserved `get`/`put` bodies are canonicalised to `given_capacity`. For example:

```text
IF LENGTH OF order >= capacity THEN
```

becomes:

```text
IF LENGTH OF order >= given_capacity THEN
```

and compiles to:

```python
if len(self.order) >= self.given_capacity:
```

The constructor parameter remains named `capacity`. Quoted text and explanatory comments are not treated as state references.

## Boundary

This release retains the existing compatibility mapping from `CLASS ... ACCEPTS(capacity)` to a Python `__init__(self, capacity)` method. The correction is that executable instance-state initialisation and later state reads must be visible in canonical pseudocode rather than appearing only in generated Python.

GC161 continues to preserve source-written `get` and `put` method bodies as established in v3.67; it does not manufacture missing LRU algorithm steps.

## Regression coverage

`tests/test_gc161_visible_capacity_state_v3_68.py` verifies that:

- canonical pseudocode contains `given_capacity <- capacity`;
- generated Python contains exactly one `self.given_capacity = capacity`;
- no silent `self.capacity = capacity` field is introduced;
- later executable `capacity` reads become `given_capacity`;
- quoted text is not renamed;
- ordinary legacy class parameter lowering outside this explicit-state case remains backwards compatible.

## Validation

- pytest: 897 passed, 3 skipped, 5 subtests passed;
- unittest: 301 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.
