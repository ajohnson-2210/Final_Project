# NL-FDEP v3.50 release record

## Scope

v3.50 performs the approved behaviour-neutral consolidation phase only. Frozen AJ_24038155 Dialect v1.1, parser semantics, compiler semantics, compatibility acceptance boundaries, and historical GC rule IDs remain unchanged.

## Shared structural scanner

The compatibility layer now has one quote-aware balanced-delimiter helper and one shared implementation for:

- top-level comma splitting across `()`, `[]`, and `{}`;
- recognising one outer parenthesis pair;
- RETURN/OUTPUT multi-value tuple-surface splitting;
- balanced single-argument member calls used by the existing evidenced `.append(...)`, `.add(...)`, stack `.push(...)`/`.push_back(...)`, and camelCase `pushBack(...)` paths;
- GC220's nested square-bracket indexed-write scan.

The two previously duplicated RETURN/OUTPUT helper triplets now delegate to this shared machinery. Historical transformation IDs and rendered AJ remain unchanged.

## Shared lexical evidence context

`LexicalEvidenceContext` centralises source-proven collection/shape facts and supports:

- routine-local frames;
- inherited readable evidence for closure-style nested routines;
- formal-parameter shadowing of inherited evidence;
- direct-rebind invalidation;
- typed evidence buckets for list, stack, set, dictionary, deque, and matrix facts.

Existing evidence-gated compatibility paths migrated to the shared representation include GC232, GC235, GC237 and GC247. Existing source-wide evidence collectors for list/stack, set-tuple insertion, and dictionary `.GET` canonicalisation also use the same fact representation. This is an implementation consolidation only; accepted and refused source forms are unchanged.

GC245 remains semantically separate because its proof is caller-to-formal-parameter evidence rather than ordinary lexical variable state.

## Matrix allocation renderer consolidation

GC246 (`N x N grid initialized to 0`) and GC249 (`rows x cols matrix filled with 0`) retain their distinct exact surface recognisers and their original transformation IDs. Their identical line traversal, audit-record creation and `CALL create_matrix(rows, cols, 0)` rendering now share one internal renderer. Their existing refusal boundaries remain separate.

## Deliberately deferred semantic phase

The historical globally permissive simple collection method rules (for example unguarded `.append`, `.add`, `.push`, queue/deque spellings) are not tightened in v3.50. Moving those onto evidence-gated dispatch is a semantic behaviour change and remains a separately approvable phase.

## Validation

- historical focused regressions across the migrated scanner/evidence/matrix paths: 59 passed;
- new consolidation/refusal/inheritance tests: 7 passed;
- representative v3.49-v3.50 differential check: processed source and transformation audit records were exactly identical;
- full pytest suite: 805 passed, 3 skipped, 5 subtests passed;
- full unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 805 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
