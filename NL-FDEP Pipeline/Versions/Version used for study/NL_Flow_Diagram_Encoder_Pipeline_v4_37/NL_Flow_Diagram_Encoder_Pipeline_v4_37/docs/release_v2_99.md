# NL-FDEP v2.99 release record

## Scope

v2.99 generalises the pre-existing negative-infinity compatibility normalisation so the explicit identifier-shaped sentinel `NEGATIVE_INFINITY` converges on the same canonical AJ representation as the already-supported `-infinity` surface.

The motivating occurrence is source_e Algorithm 15 (second largest). The implementation is corpus-wide and contains no model/file/algorithm/routine-specific condition.

## Behaviour

- `x = NEGATIVE_INFINITY` / `x <- NEGATIVE_INFINITY` -> `x <- CALL negative_infinity()`.
- Existing `x = -infinity` / `x <- -infinity` surfaces continue to use the same canonical form.
- Matching is case-insensitive for the sentinel surface.
- Member access, longer identifiers and arbitrary bare reads are not reclassified.
- Existing compiler lowering remains `float('-inf')`.

## Audit classification

source_e 15: **PASS AFTER CONSERVATIVE NEGATIVE-INFINITY REPRESENTATION RECOVERY**.

- semantic inference: NO NEW SEMANTIC INFERENCE
- algorithmic reconstruction: NO
- source logic correction: NO
- dialect change: NO

## Validation

Working tree:

- pytest: **456 passed, 3 skipped, 5 subtests passed**
- unittest: **255 passed, 1 skipped**

Fresh extraction from packaged ZIP:

- pytest: **456 passed, 3 skipped, 5 subtests passed**
- unittest: **255 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
