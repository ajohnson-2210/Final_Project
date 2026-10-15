# GC214 — provable redundant-uniqueness abstraction alignment

## Purpose

GC214 addresses a narrow compatibility case in which a model response explicitly calls an undefined `unique(result)` helper at return time even though the supplied routine has already mechanically established the complete uniqueness postcondition for `result`.

The rule is not a generic undefined-routine recovery and is not a general `unique(x) -> x` rewrite.

## Approved alignment

When the proof conditions below all hold:

```text
RETURN CALL unique(result)
```

may align to:

```text
RETURN result
```

No set conversion, new deduplication pass, or helper implementation is introduced. The order constructed by the source is preserved.

## Required proof conditions

Within the same routine and before the candidate return:

1. the returned identifier is explicitly initialised exactly once as `EMPTY LIST`;
2. at least one `APPEND value TO result` occurs after that initialisation;
3. every such append is protected by a matching `value NOT IN result` condition;
4. the proving guard is re-evaluated before the append — a loop may not open beneath the guard and repeat the append without re-checking it;
5. one proving guard may not justify multiple appends to the same result;
6. the result is not rebound, written through an index, mutated through `INSERT`, aliased, passed to an unknown call, or exposed through an unknown member call before return.

If any condition is absent, GC214 refuses the alignment and leaves `CALL unique(...)` intact.

## Semantic boundary

The rule removes only an overstated abstraction whose complete postcondition is already source-proven. It does not reason from the task description alone, infer a desired algorithm, or optimise arbitrary redundant code.

This is therefore recorded as `PROVABLE_POSTCONDITION_ALIGNMENT / REDUNDANT_UNIQUENESS_ABSTRACTION` with `source_proven` confidence and `semantic_change: false`.

AJ_24038155 Dialect v1.1 remains frozen and unchanged.
