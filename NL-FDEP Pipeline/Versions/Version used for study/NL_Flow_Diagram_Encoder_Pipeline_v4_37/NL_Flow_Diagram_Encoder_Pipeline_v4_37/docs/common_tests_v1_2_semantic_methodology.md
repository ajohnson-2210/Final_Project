# Common Tests v1.2 task-semantic methodology

## Evaluation principle

Common Tests v1.2 separates the algorithm task from implementation-specific I/O wrappers. The original task statement defines the canonical semantic interface. The frozen trusted baseline supplies reproducible concrete fixtures and reference behaviour, including deterministic policy details where the task statement is underspecified. LLM/model output is never used to infer its own expected answer.

## Per-algorithm evidence

Each of the 50 suites records: the original task statement; typed canonical inputs; canonical result type and semantics; fixture provenance and baseline SHA-256; automation status; and the same semantic contract for integrated human review.

The 113 historical Common Test cases are retained. A case is marked either as a task-semantic case eligible for function invocation, or as interaction/reference-only evidence. Only evaluable task-semantic cases contribute to automated semantic accuracy.

## Automated semantic accuracy

For an algorithm with E evaluable task-semantic cases and P passes:

`semantic_accuracy = 100 * P / E`

`NOT_EVALUABLE` and interaction/reference-only cases are not converted into behavioural failures. Runtime errors after a valid task invocation are failures because the algorithm was genuinely exercised.

Two dataset summaries are therefore useful and are intentionally distinct: mean per-algorithm semantic accuracy over algorithms with an automated semantic score, and aggregate semantic test accuracy over all evaluable semantic cases.

## Integrated human evaluation

Human semantic assessment remains part of the existing questionnaire for every algorithm. The reviewer sees the canonical task contract and records whether the required inputs are represented, whether the core logic is correct, whether required output semantics are represented, whether edge/domain handling is adequate, and an overall semantic assessment. This applies equally to automated successes, automated failures and `NOT_EVALUABLE` cases. The purpose is triangulation, not replacement of an automated result.

## Baseline calibration

The frozen baseline remains calibrated with the legacy PROGRAM/reference oracle, preserving comparability and provenance. Common Tests v1.2 adds semantic metadata without changing the controlled baseline algorithm behaviour. The baseline was revalidated under NL-FDEP v4.33 at 50/50 algorithms and 100.0% mean calibration.
