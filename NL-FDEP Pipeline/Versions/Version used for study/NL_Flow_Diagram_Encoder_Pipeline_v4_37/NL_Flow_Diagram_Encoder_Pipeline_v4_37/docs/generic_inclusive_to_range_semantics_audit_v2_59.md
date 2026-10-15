# v2.59 — Generic inclusive range endpoint semantics

AJ_24038155 Dialect v1.0 ranges are end-exclusive. Generic source `FOR ... TO ...` loops in the audited corpus use inclusive endpoints. v2.59 moves endpoint preservation into the generic grammar-normalisation boundary instead of relying on algorithm-specific patches.

## Rules

- Ascending inclusive source `TO U` -> canonical AJ `TO (U) + 1`.
- Explicit descending source `DOWNTO U` -> canonical AJ `TO (U) - 1 STEP -1`.
- Narrow implicit descending recovery `FROM LENGTH(x)-1 TO 0` -> `TO (0) - 1 STEP -1`; arbitrary start/end expressions are not guessed to be descending.
- Already-canonical `IN RANGE` is left unchanged, preventing double adjustment.

## Corpus audit

Previously identified endpoint-loss cases addressed: **92**.

- Generic ascending GC176: **91**
- Narrow implicit descending GC177: **1**
- Explicit DOWNTO endpoint corrections GC178 (additional same-semantics issue): **3**
- Residual endpoint-loss cases: **0**

Addressed-by-model: `{'source_a': 7, 'source_b_source_b_4.6': 17, 'source_c': 20, 'source_d': 9, 'source_e': 21, 'source_f_3.6_Plus': 18}`

## Validation

- Regression suite: **215 passed, 0 failed, 3 pre-existing warnings**
- Corpus: **182/300 = 60.7%**
- Coverage is unchanged from v2.58; this is a semantic correction to loop endpoints.
