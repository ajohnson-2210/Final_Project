# Baseline Common Behavioural Test Design v1.0

**Target:** NL-FDEP v4.21 / AJ_24038155 Dialect v1.4 / Scoring Rubric v1.1

## Purpose

This pack defines one common behavioural test set per frozen baseline algorithm. The same test file is used first to measure baseline pipeline calibration and then to measure experimental/model pseudocode pipeline behaviour against the same trusted baseline Python.

Expected outputs are intentionally omitted unless independently specified. The accepted frozen baseline Python supplies the behavioural oracle. This avoids inventing outcomes while keeping the calibration and experimental test set identical.

## Test categories

- **NORMAL** — representative main-path behaviour.
- **BRANCH** — a distinct externally exercisable decision path.
- **BOUNDARY** — source/reference-defined boundary behaviour.
- **ERROR_BEHAVIOUR** — invalid input, retry or exception-handling behaviour.
- **TERMINATION** — explicit quit/return/loop-termination behaviour.
- **STATE_MUTATION** — observable state/data-structure mutation across an operation sequence.

## Behavioural evidence adequacy (G2)

- **ADEQUATE** — normal behaviour plus meaningful externally controllable branch/boundary/error evidence.
- **PARTIAL** — useful behavioural evidence exists, but the frozen program interface prevents complete path coverage.
- **LIMITED** — usually a fixed-source/default scenario or environment-dependent run; structural C/A/F review remains important.
- **NOT_EVALUABLE** — no legitimate automated behavioural evidence is available.

G2 is an evidence-strength indicator and is not added to the C/A/F/P correctness score.

## Summary

- Algorithms: **50**
- Proposed automated tests: **113**
- Evidence adequacy: **{'LIMITED': 21, 'ADEQUATE': 11, 'PARTIAL': 18}**
- Test categories: **{'NORMAL': 32, 'BRANCH': 20, 'ERROR_BEHAVIOUR': 16, 'BOUNDARY': 20, 'STATE_MUTATION': 23, 'TERMINATION': 2}**

## Algorithm coverage plan

| Alg. | Test focus | Tests | G2 | Key limitation |
|---:|---|---:|---|---|
| 1 | NORMAL | 1 | LIMITED | Frozen program uses fixed strings, so alternate anagram/equality/empty cases are not externally injectable without changing the source. |
| 2 | NORMAL | 1 | LIMITED | Frozen program uses fixed integer 23; zero, one, powers of two and larger values cannot be injected without changing the source. |
| 3 | BRANCH, NORMAL, ERROR_BEHAVIOUR | 5 | ADEQUATE | None declared |
| 4 | NORMAL | 1 | LIMITED | Array contents and target scenario are fixed in the frozen source; empty/disjoint/duplicate variants are not externally injectable. |
| 5 | NORMAL | 1 | LIMITED | Input string is fixed; empty/no-punctuation/all-punctuation variants are not externally injectable. |
| 6 | NORMAL | 1 | LIMITED | Input string is fixed; empty-string boundary cannot be injected. |
| 7 | NORMAL | 1 | LIMITED | Sentence is fixed; repeated spaces/empty sentence/leading-trailing delimiter cases are not externally injectable. |
| 8 | NORMAL | 1 | LIMITED | Word list is fixed; duplicates/empty/single-item cases are not externally injectable. |
| 9 | NORMAL | 1 | LIMITED | Target and list are fixed; the not-found branch cannot be exercised externally. |
| 10 | NORMAL | 1 | LIMITED | Paragraph is fixed; zero-vowel/uppercase-only variants are not externally injectable. |
| 11 | NORMAL | 1 | LIMITED | IP list is fixed; empty/all-unique/all-duplicate variants are not externally injectable. |
| 12 | NORMAL | 3 | PARTIAL | The grid is internally generated; fixed seeds provide reproducibility but do not expose hand-selected edge matrices. |
| 13 | NORMAL | 1 | LIMITED | Input string is fixed; empty/single-character boundaries are not externally injectable. |
| 14 | NORMAL | 1 | LIMITED | List is fixed; empty/no-even/all-even variants are not externally injectable. |
| 15 | NORMAL | 1 | LIMITED | List is fixed; duplicate-maximum, two-item and undersized-list cases are not externally injectable. |
| 16 | NORMAL, BRANCH, BOUNDARY, ERROR_BEHAVIOUR | 5 | ADEQUATE | None declared |
| 17 | NORMAL | 1 | LIMITED | List is fixed; empty/single-value/negative-only cases are not externally injectable. |
| 18 | NORMAL | 1 | LIMITED | String is fixed; empty-string and repeated-single-character variants are not externally injectable. |
| 19 | BRANCH | 1 | LIMITED | Frozen values exercise the mixed-type branch only; numeric-numeric and string-string branches are not externally injectable. |
| 20 | NORMAL, BOUNDARY, ERROR_BEHAVIOUR | 5 | ADEQUATE | None declared |
| 21 | NORMAL, BRANCH, BOUNDARY, ERROR_BEHAVIOUR | 5 | ADEQUATE | None declared |
| 22 | NORMAL, BOUNDARY, ERROR_BEHAVIOUR | 5 | ADEQUATE | None declared |
| 23 | BRANCH, BOUNDARY, ERROR_BEHAVIOUR | 8 | ADEQUATE | None declared |
| 24 | NORMAL, ERROR_BEHAVIOUR, BRANCH | 4 | ADEQUATE | None declared |
| 25 | NORMAL | 1 | LIMITED | Input sentence is fixed; empty, all-unique and all-repeated strings are not externally injectable. |
| 26 | STATE_MUTATION | 1 | PARTIAL | Tree shape is fixed; empty-tree and single-node boundaries are not externally injectable through the program interface. |
| 27 | STATE_MUTATION | 1 | LIMITED | Matrix is fixed; 1x1, non-square and alternative square matrices are not externally injectable. |
| 28 | NORMAL | 1 | LIMITED | Array and window size are fixed; k=1, k=len(arr), invalid k and negative-only arrays are not externally injectable. |
| 29 | BRANCH | 1 | PARTIAL | Training data and embedded test sentences are fixed, but the program exercises several categories and an ambiguous/low-signal example. |
| 30 | STATE_MUTATION | 1 | PARTIAL | Corpus and model parameters are fixed; alternate corpora and empty-corpus boundaries are not externally injectable. |
| 31 | BRANCH | 1 | PARTIAL | Input text and lexical resources are fixed; alternate pronoun patterns are not externally injectable. |
| 32 | BRANCH, BOUNDARY | 5 | ADEQUATE | None declared |
| 33 | NORMAL, BRANCH, BOUNDARY, ERROR_BEHAVIOUR | 6 | ADEQUATE | None declared |
| 34 | STATE_MUTATION | 1 | PARTIAL | Embedded list cases are fixed; the helper function is not invoked through an external contract by the current program runner. |
| 35 | STATE_MUTATION | 3 | PARTIAL | The access sequence is internally random; fixed seeds provide reproducible eviction histories but cannot inject hand-crafted edge sequences. |
| 36 | BRANCH | 1 | PARTIAL | The embedded examples exercise two found targets and a missing target; alternate pivots and boundaries are fixed. |
| 37 | STATE_MUTATION | 1 | PARTIAL | The embedded sequence covers push, peek, pop and empty-stack attempts; alternative capacities/values are fixed. |
| 38 | BRANCH | 1 | PARTIAL | Embedded examples cover unique-character and no-unique-character cases; empty string is not exercised. |
| 39 | STATE_MUTATION | 1 | PARTIAL | The embedded sequence covers no-cycle, cycle creation and removal; invalid-index branches are present but not all are necessarily reached. |
| 40 | STATE_MUTATION | 1 | PARTIAL | The embedded sequence exercises transfer between stacks and FIFO order; empty-queue dequeue is not reached by the default script. |
| 41 | BOUNDARY, STATE_MUTATION, ERROR_BEHAVIOUR, TERMINATION | 6 | ADEQUATE | None declared |
| 42 | NORMAL, BRANCH, BOUNDARY | 3 | PARTIAL | The random array requires deterministic seeding; exact pair multiplicity depends on the seeded generated array. |
| 43 | BOUNDARY, BRANCH, NORMAL, ERROR_BEHAVIOUR | 4 | ADEQUATE | None declared |
| 44 | NORMAL | 3 | PARTIAL | Array values/length are internally random; seeded runs give reproducible variation but do not guarantee every restart/tie pattern. |
| 45 | STATE_MUTATION | 3 | PARTIAL | Dimensions and values are internally random; fixed seeds make them reproducible. |
| 46 | STATE_MUTATION | 3 | PARTIAL | Matrix dimensions and values are internally random; fixed seeds make the generated compatible matrices reproducible. |
| 47 | STATE_MUTATION | 3 | PARTIAL | Initial quantities and transaction quantities are internally random; fixed seeds make state transitions reproducible but do not force every exceptional stock branch. |
| 48 | ERROR_BEHAVIOUR | 1 | LIMITED | The frozen program hardcodes C:/example/start/path. A successful recursive-search fixture cannot be injected without changing the source or adding a path-virtualisation layer. |
| 49 | STATE_MUTATION | 3 | PARTIAL | Maze generation is random; fixed seeds provide reproducible mazes but do not expose arbitrary grid sizes because create_grid(11, 20) is fixed. |
| 50 | TERMINATION | 1 | LIMITED | The reference is graphical/stateful and has no stdout result representing collision avoidance. |

## Important interpretation rule

A 100% behavioural score with **LIMITED** G2 evidence is not equivalent to a 100% score with **ADEQUATE** G2 evidence. The behavioural percentage records performance on the executed common tests; G2 records how much behavioural evidence those tests provide. Structural criteria C3/A3/F2–F4 remain essential for branches that the frozen program cannot expose through its external interface.

## Reproducibility extensions

Randomised reference programs use fixed `random_seed` values. Environment-dependent tests can declare `environment` variables and `requires_modules`. These controls are study fixtures and do not change the frozen baseline source.

## Known hard cases

- Algorithm 48 hardcodes an external filesystem path; the automated test can cover the access-failure path, but successful recursive traversal requires a future path-virtualisation/fixture layer.
- Algorithm 50 is graphical/stateful. A headless startup/termination test is useful but insufficient to prove collision avoidance. Full behavioural evidence requires state-snapshot assertions over positions, velocities, obstacle distances and target changes.