# NL-FDEP v4.35 RC13

## Baseline session continuity and dependency bootstrap

RC13 changes runner workflow only. Pipeline transformation semantics, Common Tests v1.4.1, Semantic Boundary Variance, rubric scoring, Human Review, and dashboard methodology are unchanged.

### Automated dependency verification

Before Baseline benchmark or LLM study processing, the runner checks the active Python interpreter for packages declared in:

1. `requirements.txt`
2. `requirements-optional.txt`

If packages are missing, the runner identifies them and asks whether to install the requirements. Installation uses `sys.executable -m pip`, so an active `.venv` is used rather than an unrelated global Python installation. When installation is authorised, `requirements.txt` is processed first and `requirements-optional.txt` second. Installation or verification failure prevents Baseline/LLM study processing but does not corrupt existing study artefacts.

### Baseline returns to main menu

A successful standalone **Baseline benchmark folder** run now remains active in memory for the current process. After calibration completes and readiness is confirmed, the runner prints that the baseline is active and returns to the main options menu. Selecting **LLM results folder** then reuses the active baseline directly; it is not reselected or recalibrated.

The baseline path is still a procedural readiness gate only and is never forwarded to experimental semantic scoring.

### Single readiness rule

RC13 removes the historical session-only `DEGRADED_49_OF_50_OVERRIDE`.

A baseline is study-ready only when:

- all 50 baseline algorithms have current pipeline `SUCCESS` outcomes;
- every behaviourally evaluable calibration scores 100%; and
- the only permitted calibration unavailability is an explicitly `BEHAVIOURAL_NOT_EVALUATED` case produced by a pipeline-successful algorithm.

The current frozen baseline may therefore be 49/50 behaviourally evaluable while still being fully study-ready when the remaining algorithm is explicitly not behaviourally evaluable. This is not a 49/50 dependency override: pipeline processing remains 50/50 successful.

Any missing dependency, pipeline failure, stale result, other unavailable state, or evaluated calibration below 100% blocks LLM study readiness.

### Session safety preserved

The active baseline is kept only in memory for the live runner process. A temporary external runner-state file remains a crash-recovery hint only. Orderly exit clears it; a later process never silently activates the previous baseline.

### Regression coverage

RC13 adds regression coverage for:

- core/optional dependency verification and ordered installation;
- no pip invocation when requirements are already present;
- no degraded continuation after a dependency-related pipeline failure;
- acceptance of 50/50 pipeline success with 49 evaluable calibrations at 100% plus one genuine `BEHAVIOURAL_NOT_EVALUATED` case;
- Baseline menu calibration returning to the main menu; and
- immediate reuse of that active baseline by the LLM study route in the same process.

### Validation

- `pytest`: 1,322 passed, 3 skipped, 5 subtests passed.
- `unittest` with project component paths: 449 passed, 1 skipped.
- Common Tests v1.3, v1.4, and v1.4.1: byte-identical to RC12.
- Release checksum manifest: verified before packaging.
