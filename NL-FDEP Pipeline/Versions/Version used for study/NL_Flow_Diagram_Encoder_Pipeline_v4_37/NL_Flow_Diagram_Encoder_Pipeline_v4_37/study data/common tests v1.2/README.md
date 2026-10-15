# Packaged Common Tests v1.2

Common Tests v1.2 retains the 50-suite / 113-case v1.1 behavioural corpus and adds a task-semantic contract to every algorithm. Each test declares whether it is eligible for semantic function-level evaluation. Task-domain semantic cases use explicit baseline-derived fixtures and task-semantic oracles; the frozen trusted baseline resolves deterministic policy details where the task statement itself is underspecified. UI retry/menu/reference-only cases remain preserved as interaction evidence but are not included in function-level semantic accuracy.

The semantic contract is derived from the original task specification. Parameter names and wrapper structure are not scoring requirements. Human review uses the same contract for every algorithm, including automated NOT_EVALUABLE cases.
