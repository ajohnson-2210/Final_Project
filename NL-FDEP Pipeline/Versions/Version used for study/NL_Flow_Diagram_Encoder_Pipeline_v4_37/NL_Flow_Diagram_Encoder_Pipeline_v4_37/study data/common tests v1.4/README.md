# Common Tests v1.4 — Frozen Task-Semantic Evaluation + Semantic Boundary Variance

Common Tests v1.4 contains 50 suites and 156 declared cases. Core behavioural tests continue to use explicit pre-experiment fixtures and static expected semantic values. Experimental evaluation executes only the generated program; no baseline/reference implementation is used at runtime to derive expected values.

## Separate score streams

- **CORE_BEHAVIOURAL** contributes to task-semantic Common Test accuracy and the existing experimental semantic behavioural score.
- **SEMANTIC_BOUNDARY_PROBE** is observational and never changes core behavioural accuracy. It reports **Semantic Boundary Variance (SBV)**: the percentage of evaluable out-of-domain probes that the generated implementation accepts and processes. Runtime failures/rejections are separately classified.

The semantic contract remains authoritative for the intended domain. Baseline calibration may be used to validate the frozen pack before study runs, but baseline behaviour does not redefine the task contract and is never used as an experimental runtime oracle.
