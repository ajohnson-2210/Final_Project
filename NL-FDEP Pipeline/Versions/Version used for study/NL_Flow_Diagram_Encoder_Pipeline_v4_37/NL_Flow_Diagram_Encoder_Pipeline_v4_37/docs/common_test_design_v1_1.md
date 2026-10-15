# Baseline Common Behavioural Test Design v1.1

**Target:** NL-FDEP v4.29 / AJ_24038155 Dialect v1.4 / Scoring Rubric v1.1

## Purpose

This pack defines the common behavioural test set used first for baseline pipeline calibration and then for experimental comparison against the same trusted baseline Python. Test Design v1.1 retains the 113 tests from v1.0 and enriches G2 evidence reporting; it does not alter the frozen baseline Python or pseudocode.

## Descriptive G2 evidence profile

G2 remains non-scored. The headline result (`ADEQUATE`, `PARTIAL`, `LIMITED`, `NOT_EVALUABLE`, or `NOT_DECLARED`) is only a sortable classification. Every suite now also declares:

- an evidence summary;
- six coverage dimensions: normal path, branch behaviour, boundary behaviour, error behaviour, termination behaviour and state mutation;
- a coverage basis;
- explicit limitations;
- interpretation guidance.

At runtime, NL-FDEP v4.26 adds declared/evaluable/pass/not-evaluable counts, evidence per dimension, reproducibility strengths and an execution-aware interpretation.

Coverage dimension values are `COVERED`, `PARTIALLY_COVERED`, `NOT_COVERED`, `NOT_APPLICABLE`, and `NOT_EVALUABLE`. A missing test category is conservatively recorded as `NOT_COVERED` unless the suite explicitly declares otherwise.

## Summary

- Algorithms: **50**
- Common tests: **113**
- Headline G2 counts: **{'LIMITED': 21, 'ADEQUATE': 11, 'PARTIAL': 18}**
- Test categories: **{'NORMAL': 32, 'BRANCH': 20, 'ERROR_BEHAVIOUR': 16, 'BOUNDARY': 20, 'STATE_MUTATION': 23, 'TERMINATION': 2}**

## Interpretation rule

A behavioural score must be read together with its descriptive G2 profile. For example, 100% behavioural agreement supported by one fixed normal-path scenario is materially weaker evidence than 100% agreement supported by normal, branch, boundary and error cases. G2 describes that difference without changing the correctness percentage.

## Algorithm coverage profiles

| Alg. | Tests | Headline G2 | Declared dimensions | Principal limitation |
|---:|---:|---|---|---|
| 1 | 1 | LIMITED | normal path=COVERED | Frozen program uses fixed strings, so alternate anagram/equality/empty cases are not externally injectable without changing the source. |
| 2 | 1 | LIMITED | normal path=COVERED | Frozen program uses fixed integer 23; zero, one, powers of two and larger values cannot be injected without changing the source. |
| 3 | 5 | ADEQUATE | normal path=COVERED, branch behaviour=COVERED, error behaviour=PARTIALLY_COVERED | No specific limitation declared. |
| 4 | 1 | LIMITED | normal path=COVERED | Array contents and target scenario are fixed in the frozen source; empty/disjoint/duplicate variants are not externally injectable. |
| 5 | 1 | LIMITED | normal path=COVERED | Input string is fixed; empty/no-punctuation/all-punctuation variants are not externally injectable. |
| 6 | 1 | LIMITED | normal path=COVERED | Input string is fixed; empty-string boundary cannot be injected. |
| 7 | 1 | LIMITED | normal path=COVERED | Sentence is fixed; repeated spaces/empty sentence/leading-trailing delimiter cases are not externally injectable. |
| 8 | 1 | LIMITED | normal path=COVERED | Word list is fixed; duplicates/empty/single-item cases are not externally injectable. |
| 9 | 1 | LIMITED | normal path=COVERED | Target and list are fixed; the not-found branch cannot be exercised externally. |
| 10 | 1 | LIMITED | normal path=COVERED | Paragraph is fixed; zero-vowel/uppercase-only variants are not externally injectable. |
| 11 | 1 | LIMITED | normal path=COVERED | IP list is fixed; empty/all-unique/all-duplicate variants are not externally injectable. |
| 12 | 3 | PARTIAL | normal path=COVERED | The grid is internally generated; fixed seeds provide reproducibility but do not expose hand-selected edge matrices. |
| 13 | 1 | LIMITED | normal path=COVERED | Input string is fixed; empty/single-character boundaries are not externally injectable. |
| 14 | 1 | LIMITED | normal path=COVERED | List is fixed; empty/no-even/all-even variants are not externally injectable. |
| 15 | 1 | LIMITED | normal path=COVERED | List is fixed; duplicate-maximum, two-item and undersized-list cases are not externally injectable. |
| 16 | 5 | ADEQUATE | normal path=COVERED, branch behaviour=PARTIALLY_COVERED, boundary behaviour=COVERED, error behaviour=PARTIALLY_COVERED | No specific limitation declared. |
| 17 | 1 | LIMITED | normal path=COVERED | List is fixed; empty/single-value/negative-only cases are not externally injectable. |
| 18 | 1 | LIMITED | normal path=COVERED | String is fixed; empty-string and repeated-single-character variants are not externally injectable. |
| 19 | 1 | LIMITED | branch behaviour=PARTIALLY_COVERED | Frozen values exercise the mixed-type branch only; numeric-numeric and string-string branches are not externally injectable. |
| 20 | 5 | ADEQUATE | normal path=COVERED, boundary behaviour=COVERED, error behaviour=PARTIALLY_COVERED | No specific limitation declared. |
| 21 | 5 | ADEQUATE | normal path=COVERED, branch behaviour=PARTIALLY_COVERED, boundary behaviour=COVERED, error behaviour=PARTIALLY_COVERED | No specific limitation declared. |
| 22 | 5 | ADEQUATE | normal path=COVERED, boundary behaviour=COVERED, error behaviour=PARTIALLY_COVERED | No specific limitation declared. |
| 23 | 8 | ADEQUATE | branch behaviour=PARTIALLY_COVERED, boundary behaviour=COVERED, error behaviour=COVERED | No specific limitation declared. |
| 24 | 4 | ADEQUATE | normal path=COVERED, branch behaviour=COVERED, error behaviour=PARTIALLY_COVERED | No specific limitation declared. |
| 25 | 1 | LIMITED | normal path=COVERED | Input sentence is fixed; empty, all-unique and all-repeated strings are not externally injectable. |
| 26 | 1 | PARTIAL | state mutation=PARTIALLY_COVERED | Tree shape is fixed; empty-tree and single-node boundaries are not externally injectable through the program interface. |
| 27 | 1 | LIMITED | state mutation=PARTIALLY_COVERED | Matrix is fixed; 1x1, non-square and alternative square matrices are not externally injectable. |
| 28 | 1 | LIMITED | normal path=COVERED | Array and window size are fixed; k=1, k=len(arr), invalid k and negative-only arrays are not externally injectable. |
| 29 | 1 | PARTIAL | branch behaviour=PARTIALLY_COVERED | Training data and embedded test sentences are fixed, but the program exercises several categories and an ambiguous/low-signal example. |
| 30 | 1 | PARTIAL | state mutation=PARTIALLY_COVERED | Corpus and model parameters are fixed; alternate corpora and empty-corpus boundaries are not externally injectable. |
| 31 | 1 | PARTIAL | branch behaviour=PARTIALLY_COVERED | Input text and lexical resources are fixed; alternate pronoun patterns are not externally injectable. |
| 32 | 5 | ADEQUATE | branch behaviour=COVERED, boundary behaviour=PARTIALLY_COVERED | No specific limitation declared. |
| 33 | 6 | ADEQUATE | normal path=COVERED, branch behaviour=PARTIALLY_COVERED, boundary behaviour=PARTIALLY_COVERED, error behaviour=COVERED | No specific limitation declared. |
| 34 | 1 | PARTIAL | state mutation=PARTIALLY_COVERED | Embedded list cases are fixed; the helper function is not invoked through an external contract by the current program runner. |
| 35 | 3 | PARTIAL | state mutation=COVERED | The access sequence is internally random; fixed seeds provide reproducible eviction histories but cannot inject hand-crafted edge sequences. |
| 36 | 1 | PARTIAL | branch behaviour=PARTIALLY_COVERED | The embedded examples exercise two found targets and a missing target; alternate pivots and boundaries are fixed. |
| 37 | 1 | PARTIAL | state mutation=PARTIALLY_COVERED | The embedded sequence covers push, peek, pop and empty-stack attempts; alternative capacities/values are fixed. |
| 38 | 1 | PARTIAL | branch behaviour=PARTIALLY_COVERED | Embedded examples cover unique-character and no-unique-character cases; empty string is not exercised. |
| 39 | 1 | PARTIAL | state mutation=PARTIALLY_COVERED | The embedded sequence covers no-cycle, cycle creation and removal; invalid-index branches are present but not all are necessarily reached. |
| 40 | 1 | PARTIAL | state mutation=PARTIALLY_COVERED | The embedded sequence exercises transfer between stacks and FIFO order; empty-queue dequeue is not reached by the default script. |
| 41 | 6 | ADEQUATE | boundary behaviour=COVERED, error behaviour=COVERED, termination behaviour=PARTIALLY_COVERED, state mutation=PARTIALLY_COVERED | No specific limitation declared. |
| 42 | 3 | PARTIAL | normal path=COVERED, branch behaviour=PARTIALLY_COVERED, boundary behaviour=PARTIALLY_COVERED | The random array requires deterministic seeding; exact pair multiplicity depends on the seeded generated array. |
| 43 | 4 | ADEQUATE | normal path=COVERED, branch behaviour=PARTIALLY_COVERED, boundary behaviour=PARTIALLY_COVERED, error behaviour=PARTIALLY_COVERED | No specific limitation declared. |
| 44 | 3 | PARTIAL | normal path=COVERED | Array values/length are internally random; seeded runs give reproducible variation but do not guarantee every restart/tie pattern. |
| 45 | 3 | PARTIAL | state mutation=COVERED | Dimensions and values are internally random; fixed seeds make them reproducible. |
| 46 | 3 | PARTIAL | state mutation=COVERED | Matrix dimensions and values are internally random; fixed seeds make the generated compatible matrices reproducible. |
| 47 | 3 | PARTIAL | state mutation=COVERED | Initial quantities and transaction quantities are internally random; fixed seeds make state transitions reproducible but do not force every exceptional stock branch. |
| 48 | 1 | LIMITED | error behaviour=PARTIALLY_COVERED | The frozen program hardcodes C:/example/start/path. A successful recursive-search fixture cannot be injected without changing the source or adding a path-virtualisation layer. |
| 49 | 3 | PARTIAL | state mutation=COVERED | Maze generation is random; fixed seeds provide reproducible mazes but do not expose arbitrary grid sizes because create_grid(11, 20) is fixed. |
| 50 | 1 | LIMITED | termination behaviour=PARTIALLY_COVERED | The reference is graphical/stateful and has no stdout result representing collision avoidance. |
