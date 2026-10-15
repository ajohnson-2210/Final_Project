# source_b Algorithm 28 general deque-shorthand audit — v2.79

## Empirical study occurrence

Study source: source_b, Algorithm 28 — sliding-window maximum.

The supplied response explicitly uses a list-backed `deque` and the following deque vocabulary:

    deque <- []
    deque not empty
    deque.front
    deque.back
    REMOVE front of deque
    REMOVE back of deque
    APPEND i TO back of deque

The algorithm, queue discipline, index storage and control flow are all explicit in the response. No missing operation is reconstructed by this measure.

## v2.78 observed failure

v2.78 normalised the function, lists, range loop, inline IF body and block boundaries, but left the deque shorthand unchanged. Strict parsing then failed at:

    WHILE deque not empty ...

GC136 already provided deterministic deque conversions, but its activation gate required the flattened spellings `deque_front` and `deque_back` plus identifiers associated with a sliding-window implementation (`RESULT` and `ARR`). source_b's source instead uses the equally explicit dot spellings `deque.front` and `deque.back`, so the rule never activated.

## Root cause

The recovery capability existed, but its activation was algorithm-shaped rather than source-evidence-shaped and recognised only one spelling of explicit front/back access.

## Approved general measure

v2.79 retains the GC136 identifier for audit continuity but makes activation depend only on explicit deque evidence:

1. a variable named `deque` must already be explicitly initialised as a list (`EMPTY LIST`, `LIST [...]`, or the existing `CALL list_value(...)` compatibility representation); and
2. at least one explicit deque boundary idiom must be present.

When those safeguards hold, GC136 accepts both flattened and dot-property spellings and performs the existing deterministic conversions:

    deque not empty       -> LENGTH OF deque > 0
    deque_front           -> deque[0]
    deque.front           -> deque[0]
    deque_back            -> deque[-1]
    deque.back            -> deque[-1]
    REMOVE front of deque -> REMOVE FIRST ITEM FROM deque
    REMOVE back of deque  -> REMOVE LAST ITEM FROM deque
    APPEND x TO back of deque -> APPEND x TO deque

The transformation no longer requires `RESULT`, `ARR`, or recognition of a sliding-window algorithm.

## Back-index compatibility policy

The approved recovered representation for `deque.back` is the concise form:

    deque[-1]

The strict AJ parser already accepts both:

    deque[-1]
    deque[LENGTH OF deque - 1]

and nested forms such as:

    arr[deque[-1]]
    arr[deque[LENGTH OF deque - 1]]

Both representations are therefore retained as valid input; neither is canonicalised into the other. Regression tests verify that both parse and compile, and that the two nested forms produce the same result for the same non-empty deque.

## Audit classification

    status:
        PASS AFTER DETERMINISTIC COLLECTION-SHORTHAND RECOVERY

    source problem:
        explicit list-backed deque operations expressed with conventional
        front/back shorthand not recognised by the existing activation gate

    root cause:
        GC136 activation was algorithm-shaped and recognised only
        deque_front/deque_back, not deque.front/deque.back

    required recovery:
        activate from explicit list-backed deque evidence and accept both
        front/back spellings

    semantic inference:
        NONE

    algorithmic reconstruction:
        NO

    control flow changed:
        NO

    data structure invented:
        NO

    missing operation inserted:
        NO

    algorithm-specific parsing rule:
        NO

## Regression evidence

v2.79 includes:

- the exact source_b Algorithm 28 study occurrence;
- a non-sliding-window list-backed deque case proving the rule is general;
- a negative case showing the rule does not activate for an untyped/unbacked `deque` parameter;
- backwards compatibility for `deque_front` and `deque_back`;
- direct parser/compiler coverage for both `deque[-1]` and `deque[LENGTH OF deque - 1]`;
- behavioural equivalence coverage for `arr[deque[-1]]` and `arr[deque[LENGTH OF deque - 1]]`.

The exact study occurrence is retained in the regression source so the empirical case motivating the general measure remains auditable in version control.
