# NL-FDEP v4.21 — common behavioural tests and evidence adequacy

Pipeline: **NL-FDEP v4.21**  
Dialect: **AJ_24038155 Dialect v1.4 (unchanged)**  
Scoring rubric: **v1.1**

## Purpose

v4.21 prepares the study for the frozen 50-algorithm common behavioural test set. The same tests are used first to measure baseline pipeline calibration and then to measure experimental/model pseudocode behaviour against the same trusted baseline Python.

## Rubric v1.1

The existing 16 scored criteria C1-C4, A1-A4, F1-F4 and P1-P4 are unchanged. Rubric v1.1 adds non-scored **G2 Behavioural Evidence Adequacy** with outcomes `ADEQUATE`, `PARTIAL`, `LIMITED`, `NOT_EVALUABLE`, or `NOT_DECLARED`.

G2 measures strength of behavioural evidence rather than algorithm correctness and is never added to stage percentages. This prevents a single fixed-source execution from being interpreted as equivalent evidence to a suite that exercises normal, branch, boundary, error and termination behaviour.

P3 automatic evidence now includes tests tagged `TERMINATION` in addition to `BOUNDARY` and `ERROR_BEHAVIOUR`.

## Test metadata and reproducibility

`Algorithm n Tests.json` may now declare:

- `criteria_links` — identifies which Python-stage criteria a test supplies evidence for.
- `random_seed` — seeds Python `random` before both trusted-reference and generated-program execution.
- `environment` — controlled environment variables for the subprocess.
- `requires_modules` — declares external Python modules needed by the reference test.
- suite-level `evidence_adequacy`, `coverage_limitations`, `manual_review_targets`, and `requires_pipeline_features`.

When a reference test declares unavailable external modules, it is not used to invent behavioural expectations.

## Behavioural analysis

Per-algorithm scoring now records category-level accuracy for `NORMAL`, `BRANCH`, `BOUNDARY`, `ERROR_BEHAVIOUR`, `TERMINATION`, and `STATE_MUTATION` tests, plus G2 evidence adequacy.

## Frozen-source policy

No baseline Python or baseline pseudocode is modified by v4.21. Random seeds, environment variables and test metadata are study fixtures only.

## Known limits

Algorithm 48's frozen program hardcodes an external filesystem path. The common automated test covers its access-failure behaviour; full successful-recursion coverage would require path virtualisation/fixture support.

Algorithm 50 is graphical and stateful. A headless startup/termination test is useful but does not by itself establish collision avoidance. Full evidence would require state-snapshot assertions over drone positions, velocities, obstacle distances and mission-target transitions.
