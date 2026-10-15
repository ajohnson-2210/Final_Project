# source_b Algorithm 26 pre-literal assignment-boundary audit — v2.78

## Empirical study occurrence

Study source: source_b, Algorithm 26 — level-order binary-tree traversal.

The source contains two explicit comma-compressed assignment pairs:

    queue ← [root], result ← []
    level ← [], nextQueue ← []

The algorithmic operations, data structures and control flow are all explicit in the supplied response. No missing operation or branch is reconstructed by this change.

## v2.77 observed failure

After ordinary character and empty-list normalisation, the first pair became:

    queue <- [root], result <- EMPTY LIST

The existing GC078 recovery later split this into two statements:

    queue <- [root]
    result <- EMPTY LIST

but GC094 whole-RHS list-literal normalisation had already run. The exposed non-empty list therefore remained raw:

    queue <- [root]

which is not accepted as an AJ expression and failed parsing at the `[` token.

The second assignment pair did not expose the same parser failure because `[]` is converted to `EMPTY LIST` by the earlier unambiguous empty-list rule even while it remains embedded in the compressed line.

## Root cause

This was an ordering defect between two existing general rules:

- GC078: split multiple explicit simple assignments at top-level commas;
- GC094: canonicalise a whole-RHS non-empty list literal to `LIST [...]`.

GC094 requires a complete assignment statement. In v2.77, GC078 exposed that complete statement only after the literal pass had finished.

## Approved structural measure

v2.78 reuses the existing GC078 top-level-comma splitter and assignment-shape safeguards before literal normalisation.

The rule remains conservative:

- commas nested inside `()`, `[]` or `{}` are not statement boundaries;
- commas inside quoted strings are not statement boundaries;
- every top-level segment must independently be an explicit simple assignment;
- the later GC078 recovery remains as a fallback for assignments exposed by later compatibility processing.

No generic comma splitting was introduced.

The approved ordering is therefore:

    explicit statement-boundary recovery (GC078)
        -> literal normalisation (GC091 / GC094 / related literal rules)
        -> later compatibility/recovery passes

For the study occurrence, this exposes:

    queue <- [root]
    result <- []

before literal normalisation, allowing the existing literal rules to produce:

    queue <- LIST [root]
    result <- EMPTY LIST

A pre-existing later compatibility rule (GC157) currently represents the valid non-empty AJ list literal as:

    queue <- CALL list_value(root)

before strict parsing. v2.78 does not alter that downstream representation. It compiles deterministically to:

    queue = [root]

## Audit classification

    status:
        PASS AFTER STRUCTURAL RECOVERY

    source problem:
        multiple explicit assignments compressed onto single lines;
        non-empty list literal hidden from whole-RHS literal normalisation
        until after that pass had completed

    root cause:
        GC094 executed before GC078 exposed the individual assignment

    required recovery:
        apply existing guarded GC078 split before literal normalisation

    semantic inference:
        NONE

    algorithmic reconstruction:
        NO

    control flow changed:
        NO

    data structure invented:
        NO

    algorithm-specific parsing rule:
        NO

## Regression evidence

v2.78 regression coverage includes:

- the exact source_b Algorithm 26 source shape;
- a non-empty list RHS plus a second explicit assignment;
- ordinary `x <- 1, y <- 2` splitting;
- function-call argument commas;
- list-element commas;
- parenthesised commas;
- brace-contained commas;
- commas inside strings;
- a mixed assignment/non-assignment line that must remain unsplit.

The exact study case is retained in the regression source so the empirical occurrence that motivated the general measure remains auditable in version control.
