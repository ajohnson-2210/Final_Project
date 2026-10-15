# source_b Algorithm 37 audit — v2.81

## Scope and evidence role

This record continues the version-controlled audit of the source_b study responses. The exact Algorithm 37 occurrence is retained in `tests/test_source_b_algorithm37_last_item_shorthand_v2_81.py` as focused empirical evidence for the general recovery measure. The complete raw study corpus remains external study data.

## Source occurrence

source_b describes an array-backed stack with nested `push`, `pop` and `peek` functions. Two source statements use explicit natural-language last-item shorthand:

    REMOVE and RETURN last item of data
    RETURN last item of data

The first statement explicitly requires destructive removal of the final item and return of that same item. The second explicitly requires a non-destructive read of the final item.

## Approved deterministic interpretation

For an explicitly list-backed collection `data`:

    REMOVE and RETURN last item of data

is canonicalised as:

    RETURN REMOVE LAST ITEM FROM data

and compiles to the Python behaviour:

    return data.pop(-1)

Likewise:

    RETURN last item of data

is canonicalised as:

    RETURN data[-1]

and compiles to:

    return data[-1]

No semantic choice is introduced: the source explicitly supplies both the collection boundary (`last item`) and, in the first form, the destructive-and-return behaviour.

## Root cause in v2.80

GC139 already contained Stack-specific versions of these rewrites, but its activation depended on recognising a particular fully canonical nested Stack function shape before later grammar normalisation had produced that shape for the exact source_b source. Consequently the same explicit shorthand was left unprocessed.

## Approved general measure — GC139

v2.81 removes the algorithm-specific Stack header gate. GC139 now applies the two exact last-item idioms only when the referenced collection is already evidenced as list-backed by canonical source information such as:

- `name <- EMPTY LIST`;
- `name <- LIST [...]`;
- `name <- CALL list_value(...)`; or
- an explicit `name AS LIST` declaration.

The rule does not activate for undeclared collections or set-backed collections. It does not infer an ordering for a set, create a list where none was supplied, or invent stack semantics from an arbitrary variable name.

## Remaining Algorithm 37 interface omission

After the structural shorthand is recovered, the exact source_b source parses and compiles to nested Python functions equivalent to:

    def Stack():
        data = []
        def push(item): ...
        def pop(): ...
        def peek(): ...

The source does not return `push`, `pop` or `peek`, attach them to an object, or otherwise expose them. Therefore calling `Stack()` returns `None`.

v2.81 intentionally does **not** repair that omission. Returning a tuple/dictionary of functions or converting the structure to a class would require interface reconstruction not supplied by the source.

## Classification

    Algorithm:
        source_b 37 — Stack Using Array

    structural last-item shorthand:
        PASS AFTER DETERMINISTIC STRUCTURAL RECOVERY

    destructive source instruction:
        REMOVE and RETURN last item of data

    recovered behaviour:
        return data.pop(-1)

    non-destructive source instruction:
        RETURN last item of data

    recovered behaviour:
        return data[-1]

    semantic inference for these operations:
        NONE

    algorithmic reconstruction for these operations:
        NO

    general pipeline measure:
        YES — GC139 list-backed last-item shorthand

    remaining external Stack interface supplied:
        NO

    interface reconstruction performed:
        NO

    overall behavioural study outcome:
        EXPECTED FAIL — INCOMPLETE EXECUTABLE DATA-STRUCTURE INTERFACE

The distinction is deliberate: a recoverable statement-level shorthand is recovered and evidenced, while the unrelated missing public interface remains a genuine source limitation rather than being silently invented.

## Regression evidence

v2.81 includes regressions for:

- the exact source_b Algorithm 37 occurrence;
- destructive last-item return compiling to `pop(-1)`;
- non-destructive last-item read compiling to `[-1]`;
- the same rule on a differently named `AS LIST` parameter;
- mutation/non-mutation behavioural checks;
- no recovery for an undeclared collection;
- no recovery for a set-backed collection; and
- confirmation that the exact source_b `Stack()` still returns `None` because no interface is invented.

## Subsequent audit revision — v2.82

The interface conclusion above is retained as the historical v2.81 decision, but it was revisited during the continuing evidence audit. Direct execution established that the literal outer-function interpretation produces `None` and makes the source-supplied `push`, `pop` and `peek` operations undiscoverable. The surrounding evidence — an outer zero-argument abstraction named `Stack`, persistent shared state, and multiple nested operations that all act on that state — was subsequently approved as sufficient evidence of a stateful ADT structural misclassification. v2.82 therefore adds a separate GC196 recovery described in `source_b_algorithm37_stateful_adt_recovery_v2_82.md`. GC139's statement-level last-item interpretation is unchanged.
