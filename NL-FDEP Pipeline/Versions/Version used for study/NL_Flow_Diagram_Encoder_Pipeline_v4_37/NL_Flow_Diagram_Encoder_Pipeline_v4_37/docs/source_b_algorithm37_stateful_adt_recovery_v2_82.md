# source_b Algorithm 37 stateful-ADT recovery — v2.82

## Scope and evidence role

This record documents the approved revision to the source_b Algorithm 37 audit. The exact study occurrence is retained in `tests/test_source_b_algorithm37_stateful_adt_v2_82.py` as empirical evidence for the general recovery rule. The earlier v2.81 record remains as the history of the statement-level GC139 recovery and of the interface question before it was resolved.

## Source evidence

source_b supplies an outer zero-argument construct named `Stack`, one persistent list-backed state variable `data`, and three nested operations:

    FUNCTION Stack()
        data <- []
        FUNCTION push(item)
            APPEND item TO data
        FUNCTION pop()
            ...
            REMOVE and RETURN last item of data
        FUNCTION peek()
            ...
            RETURN last item of data

All three nested operations act on the same persistent state.

## Literal-function execution evidence

If the outer construct is interpreted literally as a Python function, the generated shape is equivalent to:

    def Stack():
        data = []
        def push(item): ...
        def pop(): ...
        def peek(): ...

There is no outer return. Therefore `Stack()` evaluates to `None`. The nested functions exist only in the invocation's local scope and are not properties of either the outer function object or its returned value. Consequently a normal stack use such as `stack = Stack(); stack.push(1)` cannot work: `stack` is `None` and no `push`, `pop` or `peek` property is discoverable from it.

This runtime result is evidence that the source's outer `FUNCTION Stack()` spelling cannot represent the stateful interface that the same source explicitly supplies.

## Approved interpretation

The audit therefore classifies the outer function keyword as a recoverable structural misclassification of a stateful abstract data type:

- outer stateful container -> `CLASS`;
- source-supplied state assignment -> constructor/class state;
- nested source-supplied operations -> methods;
- method bodies -> unchanged except for already-approved independent normalisation such as GC139.

The pipeline's existing executable class representation is:

    CLASS Stack ACCEPTS()
        data <- EMPTY LIST
        FUNCTION push ACCEPTS(item)
            APPEND item TO data
        ENDFUNCTION
        FUNCTION pop ACCEPTS()
            IF LENGTH OF data == 0 THEN
                RETURN STRING("Underflow")
            ENDIF
            RETURN REMOVE LAST ITEM FROM data
        ENDFUNCTION
        FUNCTION peek ACCEPTS()
            IF LENGTH OF data == 0 THEN
                RETURN STRING("Empty")
            ENDIF
            RETURN data[-1]
        ENDFUNCTION
    ENDCLASS

The existing ClassNode compiler interprets the top-level class assignment as constructor state and nested functions as methods, producing behaviour equivalent to:

    class Stack:
        def __init__(self):
            self.data = []

        def push(self, item):
            self.data.append(item)

        def pop(self):
            if len(self.data) == 0:
                return "Underflow"
            return self.data.pop(-1)

        def peek(self):
            if len(self.data) == 0:
                return "Empty"
            return self.data[-1]

No new stack operation is invented. The public operation names, their parameters, shared state and all method behaviour are supplied by the source.

## General measure — GC196

GC196 is deliberately not a generic `nested functions -> class` rewrite. It activates only when all of the following structural evidence is present after ordinary block recovery:

1. the entire source consists of one top-level zero-argument function container;
2. at least one explicit plain state assignment occurs before nested operations;
3. at least two nested functions are supplied;
4. every nested function references at least one of the declared persistent state names;
5. the outer body contains no meaningful executable statement other than state declarations and the nested functions;
6. in particular, an outer return, call, output or control-flow operation prevents reclassification;
7. nested function bodies are preserved rather than synthesised.

When those conditions are met, GC196 changes only the matching outer `FUNCTION ... ENDFUNCTION` pair to `CLASS ... ENDCLASS`.

## Interaction with GC139

GC139 remains responsible only for the independently approved explicit last-item shorthand:

    REMOVE and RETURN last item of data

becomes a destructive return and compiles to:

    return self.data.pop(-1)

while:

    RETURN last item of data

remains non-destructive and compiles to the final-item read.

GC196 does not duplicate or broaden GC139.

## Behavioural evidence

The exact recovered Stack is instantiated and exercised in regression tests:

    stack = Stack()
    stack.push(3)
    stack.push(5)
    stack.peek()  -> 5
    stack.pop()   -> 5
    stack.peek()  -> 3

The tests also assert that `push`, `pop` and `peek` are discoverable callable attributes of the recovered instance.

## Negative safeguards

v2.82 includes negative regressions demonstrating that GC196 does not activate for:

- a stateful outer function with only one nested helper;
- multiple nested functions where one does not use the shared state;
- an outer function that explicitly returns a value; or
- an outer function containing its own control flow outside the nested operations.

A differently named zero-argument stateful container (`Bag`) is included as a positive generalisation case so the rule is not dependent on the names `Stack`, `push`, `pop` or `peek`.

## Classification

    Algorithm:
        source_b 37 — Stack Using Array

    status:
        PASS AFTER STATEFUL-ADT STRUCTURAL RECOVERY

    source issue:
        class-like stateful abstraction expressed as an outer FUNCTION
        containing persistent state and nested operations

    literal function interpretation:
        unusable as the supplied ADT interface; Stack() returns None and
        does not expose push/pop/peek

    recovered interpretation:
        outer container -> CLASS
        persistent assignment -> instance state
        nested operations -> methods

    semantic inference:
        LIMITED STRUCTURAL INFERENCE, evidence constrained

    algorithmic reconstruction:
        NO

    control flow changed:
        NO

    operations invented:
        NO

    interface invented:
        NO — push/pop/peek and their signatures are explicit in source

    pipeline measure:
        GC196 general zero-argument stateful-ADT container recovery

    GC139 last-item recovery:
        retained unchanged

## Subsequent canonical-grammar refinement — v2.83

The v2.82 behavioural conclusion remains valid, but its emitted class text used the pipeline's historical internal class representation. During the continuing audit this was corrected to the frozen AJ v1.0 class grammar. v2.83 emits `PROPERTY`, a zero-argument `CONSTRUCTOR` that retains the source's internal empty-state initialisation, and `METHOD` declarations with `THIS.<property>` state access. See `source_b_algorithm37_canonical_class_grammar_recovery_v2_83.md`. No constructor parameter is inferred.
