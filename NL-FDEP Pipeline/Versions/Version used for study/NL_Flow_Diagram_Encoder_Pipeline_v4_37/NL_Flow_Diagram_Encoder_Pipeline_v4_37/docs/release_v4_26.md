# NL-FDEP v4.26 — strict benchmark standard restoration

Pipeline: **NL-FDEP v4.26**  
Dialect: **AJ_24038155 Dialect v1.4 (unchanged)**  
Scoring rubric: **v1.1 (unchanged)**  
Scoring schema: **v1.4 (unchanged)**  
Common Test Design: **v1.1 (50 suites / 113 tests, unchanged)**

## Purpose

v4.26 restores the benchmark-processing rule used by the successful v4.22 baseline workflow: baseline benchmark pseudocode is processed under `AJ_DIALECT_STRICT`. The benchmark corpus defines the AJ_24038155 Dialect v1.4 reference standard, so generic compatibility recovery must not rewrite it before calibration.

## Behaviour

- Baseline Benchmark Folder runs use `AJ_DIALECT_STRICT` automatically.
- CLI baseline processing also defaults to `AJ_DIALECT_STRICT`.
- Experimental/LLM pseudocode retains its independently selected profile.
- Baseline calibration provenance includes the profile; Generic-profile calibration artefacts are stale under v4.26.
- Packaged Common Tests v1.1 remain canonical for compatible baselines.
- A measured behavioural calibration remains a valid measurement even when its percentage is below 100%.
- Algorithms without an evaluated baseline calibration remain `NOT_EVALUABLE` for baseline-relative comparison rather than receiving an invented score.

## Research rationale

The benchmark is the declared comparison standard. Applying generic compatibility transformations to that standard would alter the reference representation before measurement. Strict benchmark processing preserves the declared dialect boundary, while compatibility profiles remain available for experimental sources where recovery is part of the evaluated pipeline behaviour.
