# Common Tests v1.3 Semantic Boundary Audit

**Pipeline:** NL-FDEP v4.35 RC7  
**Scope:** Algorithms 1–50, Common Tests v1.3  
**Audit objective:** determine where the original task contract supports (a) stronger in-domain behavioural coverage and (b) a separate semantic-boundary variance measure.

## Executive conclusion

- A separate semantic-boundary measure is **immediately defensible for 16 algorithms**: 2, 4, 12, 20, 22, 23, 27, 28, 33, 35, 36, 41, 43, 44, 45, 46.
- **3 additional algorithms** (15, 17, 49) could support it after the semantic contract is clarified.
- **5 algorithms** (11, 29, 30, 48, 50) have potentially interesting out-of-domain behaviour, but it should remain descriptive until their contracts/observers are richer.
- The remaining algorithms should primarily receive **additional in-domain behavioural tests**, not an artificial out-of-domain score.
- **22 suites contain stale “cannot be injected / not externally injectable” wording** even though v1.3 semantic fixtures are function-invocation based.
- Three high-priority metadata/test defects were found: **Algorithm 33 zero handling**, **Algorithms 20/22 positive-integer boundary classification**, and **Algorithm 40 empty-queue limitation wording**.

## Proposed measurement model

Keep the existing behavioural measures intact, and add a separate probe stream rather than folding these tests into the existing score immediately.

**Core behavioural stream**: valid inputs inside the task contract. This is where normal, branch, valid boundary, state-mutation and specified error behaviour belong.

**Semantic boundary probe stream**: inputs deliberately outside an explicit task-domain constraint. Each probe should be classified as one of:
- `OUT_OF_DOMAIN_ACCEPTED` — implementation produces an ordinary semantic result outside the stated contract;
- `CONTROLLED_REJECTION` — implementation explicitly rejects/signals unsupported input;
- `INCIDENTAL_FAILURE` — execution fails, but not through a clear semantic rejection;
- `NOT_EVALUABLE`.

Recommended descriptive metric:

> **Semantic Boundary Variance (SBV) % = OUT_OF_DOMAIN_ACCEPTED probes / evaluable boundary probes × 100**

A higher SBV means the generated implementation extends further beyond the specified semantic domain. It should initially be treated as **descriptive variance, not a penalty**. This avoids penalising useful generalisation while still making divergence from the task contract visible.

The baseline may be used **before experimental runs** to validate that candidate probes are executable and to help freeze fixtures/observers, but it must not redefine the semantic domain and must not be used as a runtime experimental oracle.

## High-priority defects to correct before adding SBV

### Algorithm 33 — square root
- Contract input: `NON_NEGATIVE_INTEGER`.
- Therefore **0 is a valid in-domain value** and should produce floor square root `0`.
- Current Common Tests classify zero as an error/retry case. This contradicts the contract and should be corrected. Negative input can become an SBV probe.

### Algorithm 20 — divisors
- Contract input: `POSITIVE_INTEGER`.
- Current suite includes zero and negative values as ordinary `BOUNDARY` cases following frozen-reference behaviour.
- Those values are outside the declared semantic domain. They should move to the boundary-probe stream if SBV is adopted, rather than contributing to core behavioural coverage.

### Algorithm 22 — factorial
- Contract input: `POSITIVE_INTEGER`, but the suite tests zero.
- This needs a specification decision before scoring: either retain `POSITIVE_INTEGER` and treat zero as outside-domain, or revise the contract to `NON_NEGATIVE_INTEGER` if `0! = 1` is intended.
- Negative values remain outside-domain in either interpretation.

### Algorithm 40 — queue using two stacks
- The current operation fixture **does reach an empty dequeue** and expects `EMPTY`.
- The coverage limitation currently says empty-queue dequeue is not reached. That statement is incorrect and should be updated; the coverage declaration should also reflect this state-boundary evidence.

### Legacy injection wording
Algorithms 1, 2, 4–8, 10–11, 13–15, 17–19, 25–28, 30–31 and 48 contain wording asserting that alternate fixtures “cannot be injected” or are “not externally injectable”. In v1.3 this is stale: semantic fixtures can now be supplied through the function-invocation layer for automatable tasks. The limitations should instead state which cases are simply **not currently exercised by the frozen suite**.

## Algorithm-by-algorithm audit

| Alg | Boundary suitability | Recommended score stream | In-domain additions | Out-of-domain / variance probe | Key audit note |
|---:|---|---|---|---|---|
| 1 | CORE_ONLY | CORE_BEHAVIOURAL | Add empty/equal/repeated-character/case-sensitive cases. | None beyond generic type mismatch. | Stale injection wording. |
| 2 | HIGH | BOUNDARY_VARIANCE | Add 0, 1, powers of two, larger values. | Negative integer. | Current single fixture is 23; stale injection wording. |
| 3 | CORE_ONLY | CORE_BEHAVIOURAL | Current branch coverage is comparatively strong; optionally add extreme/negative years only if task semantics define them. | No useful semantic boundary beyond non-integer type. | No major boundary defect. |
| 4 | HIGH | BOUNDARY_VARIANCE | Add empty, disjoint, duplicates, repeated intersections. | Supply an unsorted array to test extension beyond the sorted-array contract. | Stale injection wording; sorted precondition comes from task statement. |
| 5 | CORE_ONLY | CORE_BEHAVIOURAL | Add empty, no-punctuation, all-punctuation, mixed Unicode only if specified. | No meaningful task-specific out-of-domain probe. | Stale injection wording. |
| 6 | CORE_ONLY | CORE_BEHAVIOURAL | Add empty and single-character strings. | No meaningful task-specific out-of-domain probe. | Stale injection wording. |
| 7 | CORE_ONLY | CORE_BEHAVIOURAL | Add empty, repeated spaces, leading/trailing delimiters, punctuation policy cases. | No meaningful task-specific out-of-domain probe. | Stale injection wording. |
| 8 | CORE_ONLY | CORE_BEHAVIOURAL | Add empty, singleton, duplicates, mixed case if case policy is defined. | Non-string elements are generic type violations, not useful semantic-boundary evidence. | Stale injection wording. |
| 9 | CORE_ONLY | CORE_BEHAVIOURAL | Add target absent, first/last element, duplicates, empty list. | No meaningful task-specific out-of-domain probe. | Current suite misses not-found branch. |
| 10 | CORE_ONLY | CORE_BEHAVIOURAL | Add no-vowel, uppercase-only, empty, mixed-case cases. | No meaningful task-specific out-of-domain probe. | Stale injection wording. |
| 11 | DESCRIPTIVE_ONLY | DESCRIPTIVE_BOUNDARY | Add empty, all unique, all duplicate. | Malformed IP string could be probed, but rejection semantics are not defined. | Do not score malformed-IP behaviour until contract specifies validation. |
| 12 | HIGH | BOUNDARY_VARIANCE | Add 1×1, 2×2 and hand-selected matrices in addition to seeded cases. | Rectangular or ragged matrix; optional N/dimension mismatch where adapter supplies N. | Current seeded coverage is useful but does not directly test the square constraint. |
| 13 | CORE_ONLY | CORE_BEHAVIOURAL | Add empty, singleton, repeated characters. | No meaningful task-specific out-of-domain probe. | Stale injection wording. |
| 14 | CORE_ONLY | CORE_BEHAVIOURAL | Add empty, no-even, all-even, negatives, zero. | No meaningful task-specific out-of-domain probe. | Stale injection wording. |
| 15 | MODERATE | BOUNDARY_VARIANCE_AFTER_CONTRACT_CLARIFICATION | Add two-item, duplicate maximum, negatives, ties. | Fewer than two distinct values. | Contract should encode the minimum-two-distinct-values precondition before scoring this boundary. |
| 16 | CORE_ONLY | CORE_BEHAVIOURAL | Current 48/18, coprime, zero and negative coverage is strong. | No useful task-specific boundary beyond non-integer input. | No major boundary defect. |
| 17 | MODERATE | BOUNDARY_VARIANCE_AFTER_CONTRACT_CLARIFICATION | Add singleton, negatives, zeros, mixed values. | Empty list, if contract is clarified to NON_EMPTY_ARRAY. | Empty-list semantics are currently undefined by the contract. |
| 18 | CORE_ONLY | CORE_BEHAVIOURAL | Add empty and repeated-single-character cases. | No meaningful task-specific out-of-domain probe. | Stale injection wording. |
| 19 | CORE_ONLY | CORE_BEHAVIOURAL | Add numeric/numeric and string/string branches. | No meaningful semantic boundary because contract accepts ANY. | Stale injection wording. |
| 20 | HIGH | BOUNDARY_VARIANCE | Core tests should cover 1, prime, composite and large positive values. | 0 and negative integers. | AUDIT DEFECT: current zero/negative cases are labelled ordinary BOUNDARY despite being outside POSITIVE_INTEGER. |
| 21 | CORE_ONLY | CORE_BEHAVIOURAL | Current positive, zero and negative coverage is strong. | No useful numeric boundary because all integers are valid. | No major boundary defect. |
| 22 | HIGH_SPEC_CONFLICT | BOUNDARY_VARIANCE_AFTER_CONTRACT_RESOLUTION | Core positive tests: 1, 2, 5, larger manageable values. | Negative integer; zero depends on contract decision. | AUDIT DEFECT: zero is currently tested despite POSITIVE_INTEGER; decide whether contract should instead be NON_NEGATIVE_INTEGER because 0! = 1. |
| 23 | HIGH | BOUNDARY_VARIANCE | Keep threshold cases 0/60/70/80/100 and representative interiors. | Scores below 0 and above 100. | Current out-of-range tests already exist; retag into boundary stream to avoid double counting if SBV is introduced. |
| 24 | CORE_ONLY | CORE_BEHAVIOURAL | Weak passwords, exact-8, missing uppercase/digit are all valid inputs whose result is False. | No semantic out-of-domain probe is needed. | Do not mistake invalid passwords for invalid function inputs. |
| 25 | CORE_ONLY | CORE_BEHAVIOURAL | Add empty, all unique, all repeated, repeated patterns. | No meaningful task-specific out-of-domain probe. | Stale injection wording. |
| 26 | CORE_ONLY | CORE_BEHAVIOURAL | Add empty tree, singleton, skewed tree and sparse tree. | Malformed tree representation is an adapter/type issue, not a task-semantic boundary. | Stale injection wording. |
| 27 | HIGH | BOUNDARY_VARIANCE | Add 1×1, 2×2, alternative 3×3 and 4×4 valid square cases. | 2×3/3×2 rectangular matrices; optionally ragged matrices as malformed probes. | Confirmed metadata defect: current “not externally injectable” wording is stale. 2×3 acceptance should be recorded as semantic boundary extension, not core correctness. |
| 28 | HIGH | BOUNDARY_VARIANCE | Add k=1, k=len(array), singleton array, negative-only arrays. | k<=0; k>len(array); empty-array/window combinations after relation is frozen. | Stale injection wording; relative array/window constraint should be formalised. |
| 29 | DESCRIPTIVE_ONLY | DESCRIPTIVE_BOUNDARY | Add multiple categories, ambiguous/low-signal texts, unseen wording using frozen corpus. | Empty/unlabelled training corpus or unknown category schema, but behaviour is library/spec dependent. | Do not score boundary variance until corpus/category constraints are formalised. |
| 30 | DESCRIPTIVE_ONLY | DESCRIPTIVE_BOUNDARY | Add alternate frozen corpora and small-corpus cases if deterministic. | Empty corpus or insufficient vocabulary, but semantics depend on model/library requirements. | Stale injection wording; contract needs richer corpus constraints before SBV. |
| 31 | CORE_ONLY | CORE_BEHAVIOURAL | Add alternate pronoun/noun patterns, no-pronoun and ambiguous cases. | No useful task-specific out-of-domain probe. | Stale injection wording. |
| 32 | CORE_ONLY | CORE_BEHAVIOURAL | Current who/where/what/how-many/unanswerable coverage is comparatively strong; add paraphrases if desired. | Empty/malformed text is not a meaningful separate boundary without explicit contract. | No major boundary defect. |
| 33 | HIGH_CRITICAL | BOUNDARY_VARIANCE | Core must include 0→0, 1, perfect and non-perfect squares. | Negative integer. | CRITICAL CONTRACT/TEST DEFECT: zero is valid under NON_NEGATIVE_INTEGER but current suite treats zero as rejected input. |
| 34 | CORE_ONLY | CORE_BEHAVIOURAL | Add empty/disjoint/duplicate-heavy cases. | No meaningful task-specific out-of-domain probe. | Current helper invocation limitation can be improved but is not a boundary issue. |
| 35 | HIGH | BOUNDARY_VARIANCE | Add capacity=1, repeated access, overwrite/update and hand-crafted eviction sequences. | capacity<=0. | Seeded runs should be supplemented with direct deterministic edge sequences. |
| 36 | HIGH | BOUNDARY_VARIANCE | Add pivot=0, pivot=1, pivot=n-1, singleton, target absent/present. | Array that is not a rotation of a sorted array. | Structural input precondition is explicit in contract type. |
| 37 | CORE_ONLY | CORE_BEHAVIOURAL | Keep empty pop/peek, add singleton and interleaved pushes/pops. | Unknown operation tokens are interface-schema errors, not useful semantic variance. | Empty-stack handling belongs in core state-boundary behaviour. |
| 38 | CORE_ONLY | CORE_BEHAVIOURAL | Add empty, singleton, all repeated and first/last unique cases. | No meaningful task-specific out-of-domain probe. | Current examples already cover unique and no-unique. |
| 39 | CORE_ONLY | CORE_BEHAVIOURAL | Add empty list, singleton no-cycle, self-cycle, tail-to-head and middle cycle. | Malformed list encoding or invalid helper indices are adapter/API issues. | Do not use helper invalid-index branches as semantic-boundary score. |
| 40 | CORE_ONLY_METADATA_DEFECT | CORE_BEHAVIOURAL | Keep FIFO transfer plus empty dequeue; add singleton/interleaving. | Unknown operation tokens are interface-schema errors, not useful semantic variance. | AUDIT DEFECT: current fixture DOES reach empty dequeue and expects EMPTY, but coverage limitation says it is not reached. |
| 41 | HIGH | BOUNDARY_VARIANCE | Core: N=1, N=2 no-solution, N=3 no-solution, N=4+ solutions. | N<=0. | Menu/input errors are UI robustness and should remain separate from semantic N boundary. |
| 42 | CORE_ONLY | CORE_BEHAVIOURAL | Add multiple pairs, duplicates, empty/single arrays, no match. | No meaningful task-specific out-of-domain probe. | Seeded cases are reasonable but hand-crafted multiplicity cases would improve evidence. |
| 43 | HIGH | BOUNDARY_VARIANCE | Core N=1,2,3 and larger manageable N. | N<=0. | Current nonnumeric retry is UI error; add explicit semantic N boundary probes. |
| 44 | HIGH | BOUNDARY_VARIANCE | Add singleton, all negative, all zero, tied maxima and mixed signs. | Empty array. | Current seeded runs do not exercise the explicit NON_EMPTY boundary. |
| 45 | HIGH | BOUNDARY_VARIANCE | Add 1×1, square and rectangular equal-size matrices, zeros/negatives. | Mismatched matrix dimensions. | Equal-size constraint is explicit in task/result semantics though not encoded in individual input type strings. |
| 46 | HIGH | BOUNDARY_VARIANCE | Add 1×1, row×column, identity, rectangular compatible cases. | Incompatible inner dimensions. | Compatibility constraint is explicit in canonical semantics. |
| 47 | CORE_STATE_BOUNDARY | CORE_BEHAVIOURAL | Add purchase exactly equal to stock, purchase exceeding stock, delivery, repeated item and mixed transactions. | Unknown item / negative transaction quantity require contract clarification; do not score yet. | Over-purchase is not out-of-domain: it is a valid transaction whose required core behaviour is “stock cannot become negative”. |
| 48 | DESCRIPTIVE_ONLY | DESCRIPTIVE_BOUNDARY | Add virtualised successful recursive tree, empty tree, nested matches, no matches. | Missing physical folder/path is environmental rather than semantic-domain variance. | Current suite only exercises missing-folder behaviour; path virtualisation is needed for meaningful core testing. |
| 49 | MODERATE | BOUNDARY_VARIANCE_AFTER_CONTRACT_CLARIFICATION | Add trivial start=goal, reachable path, unreachable path, narrow passages, multiple routes. | Out-of-grid start/goal or invalid blocked endpoints could be boundary probes after contract clarification. | No-path is core behaviour, not out-of-domain. Clarify coordinate validity constraints first. |
| 50 | DESCRIPTIVE_ONLY | DESCRIPTIVE_BOUNDARY | Core needs deterministic state snapshots for safe separation, target progress and termination. | Malformed drone state / impossible destination / unsafe initial overlap require a richer contract. | Do not introduce SBV until state-snapshot semantics exist; current test only establishes startup/termination. |

## Recommended implementation sequence

1. **Correct metadata/contract defects first**: Algorithms 20, 22, 33 and 40; replace stale injection wording across the 22 affected suites.
2. **Expand valid-domain fixtures** across the limited/partial suites before interpreting SBV. This prevents a model from being well-tested outside the contract while remaining poorly tested inside it.
3. Add a test metadata field such as `evaluation_role` with at least `CORE_BEHAVIOURAL` and `SEMANTIC_BOUNDARY_PROBE`.
4. Keep the existing Common Test accuracy based on `CORE_BEHAVIOURAL` tests. Compute SBV separately from `SEMANTIC_BOUNDARY_PROBE` tests to avoid double counting.
5. Extend the semantic evaluator so boundary probes can distinguish `CONTROLLED_REJECTION`, `INCIDENTAL_FAILURE` and `OUT_OF_DOMAIN_ACCEPTED`; do not assume a specific exception type unless the original task contract requires it.
6. Use the validated baseline during **pre-experiment test authoring** to sanity-check fixtures and observers. Freeze all expected fixtures/outcomes before the six-agent study; never call the baseline during experimental scoring.
7. Re-run calibration after the Common Test pack changes and version the pack (recommended next designation: **Common Tests v1.4** rather than silently modifying v1.3).

## Interpretation for the study

The proposed SBV measure should initially be reported **alongside**, not inside, the existing Combined Behavioural Measure. For example:
- Mean Semantic Behavioural Score: 84.00%
- Aggregate Common Test Accuracy: 84.13%
- Combined Behavioural Measure: 84.07%
- Semantic Boundary Variance: 20.00%

This makes semantic extension beyond the intended domain visible without automatically treating broader behaviour as incorrect. Once the revised pack has been frozen and validated across all 50 tasks, a later methodology decision could determine whether boundary adherence should contribute to a higher-level behavioural-integrity measure.