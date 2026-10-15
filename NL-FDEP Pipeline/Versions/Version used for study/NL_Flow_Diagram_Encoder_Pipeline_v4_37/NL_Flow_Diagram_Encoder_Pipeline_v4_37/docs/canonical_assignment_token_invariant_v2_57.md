# v2.57 — Canonical assignment-token invariant

## Decision

AJ_24038155 Dialect v1.0 assignment remains strictly `<-`.

A bare `?` is **not** an AJ token, **not** an assignment alias, and must never be presented as a canonical alternative to `<-`.

## Isolated legacy exception

A small number of algorithm-specific compatibility recognisers inspect literal `?` only because the stored legacy source_a text corpus lost Unicode glyphs during serialisation. This is treated as isolated source-recovery evidence upstream of the AJ parser boundary.

This exception does not extend the AJ grammar and does not create a generic `? -> <-` rule.

Successful recovery must emit strict AJ syntax before parsing. If a bare `?` remains unresolved, the AJ lexer rejects it.

## Regression guards

- `Found ? BOOLEAN(False)` must fail AJ parsing with an unrecognised-character error.
- `Found <- BOOLEAN(False)` must parse successfully.
- The legacy Algorithm 39 recovery fixture may contain `?` in its deliberately lossy input, but processed canonical AJ must contain no `?`.

## Scope

- Grammar change: NO
- Algorithm semantic change: NO
- Generic `? -> <-` conversion: NO
- Existing isolated legacy source-recovery recognisers retained: YES

## Validation

- Regression suite: 208 passed, 0 failed, 3 pre-existing collection warnings
- Corpus: 182 / 300 (60.7%)
- source_a: 38 / 50
- Parse-classification change: 0
