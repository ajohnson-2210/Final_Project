# NL-FDEP v4.35 Release Candidate 5

v4.35 RC5 retains Common Tests v1.3 / test-spec schema v1.4, AJ_24038155 Dialect v1.5, the RC4 per-process LLM session workflow, and model-neutral frozen semantic evaluation. RC5 changes only the lifecycle semantics of the interactive runner's external baseline state and the associated regression/documentation surface.

## Session-scoped baseline state

The baseline remains a **procedural study-readiness gate only**. RC5 no longer treats `%LOCALAPPDATA%\\NL-FDEP\\runner_state.json` (or its platform-equivalent path) as a durable baseline preference.

When a study-ready baseline is established for an LLM session, the runner may write a small external state file containing the baseline path and pipeline version. In RC5 that file has the explicit purpose `SESSION_CRASH_RECOVERY_HINT` and schema version `1.1`.

The lifecycle is now:

1. Establish and validate/calibrate one study-ready baseline for the live runner process.
2. Reuse that baseline in memory for subsequent LLM datasets selected in the same session.
3. Delete `runner_state.json` after an orderly LLM **Quit**.
4. Delete it after an orderly input-selection cancellation.
5. Delete any stale hint after successful completion of a non-LLM route.
6. Do **not** persist a standalone Baseline benchmark run as the next launch's selected baseline.
7. If the process terminates unexpectedly before orderly cleanup, the state file may remain. On the next launch it is only a recovery hint: the runner displays it, requires an explicit **Use detected baseline** or **Choose baseline folder and recalibrate** decision, and revalidates current v4.35/Common Tests v1.3 readiness before any LLM batch can start.

The previous dormant `resolve_baseline_dependency()` path, whose purpose was cross-session automatic reuse, has been removed from the live RC5 codebase. The obsolete RC3 backup copy of the runner is also excluded from the RC5 package to avoid retaining contradictory historical execution logic beside the release entry point.

## Behaviour preserved from RC4

RC5 deliberately preserves the successful RC4 study-session semantics:

- baseline processing remains fixed to `AJ_DIALECT_STRICT`;
- LLM result datasets use the independently selected experimental profile, normally `GENERIC_COMPATIBILITY`;
- readiness still requires 50/50 current terminal baseline runs, 50/50 behaviourally evaluated calibrations, and 50/50 calibration scores at 100%;
- one established baseline is reused across multiple LLM datasets in the same live process;
- after each LLM batch the runner offers another LLM folder, human evaluation, or quit;
- the baseline is a procedural readiness gate only and is never forwarded to `run_llm_results_folder()` or the experimental scorer;
- experimental expected values remain the static frozen Common Tests v1.3 semantic references.

## Why RC5 changes the state lifecycle

A newly extracted release could previously appear to "already know" a baseline because the external state file survived the lifetime of an earlier release folder. RC4 made that inherited path explicit rather than silently activating it, but still left the file after a normal quit. RC5 closes that remaining gap: a normal end to the runner no longer creates baseline-selection state for the next launch.

This gives the state file one defensible role only: recovery from an unfinished session. Even in that case the file is a pointer, not proof of calibration or authorisation to use the benchmark.

## RC5 regression coverage

RC5 adds or updates tests proving that:

- orderly LLM-session return clears the external recovery hint;
- input-selection cancellation clears the hint;
- a standalone Baseline benchmark route does not persist a baseline for the next launch;
- unexpected LLM-session exceptions preserve the hint for recovery rather than deleting it unconditionally;
- the recovery-hint payload is schema `1.1` and declares `SESSION_CRASH_RECOVERY_HINT`;
- legacy RC4/v4.34 state without that purpose marker remains readable only as a detection hint;
- RC4's explicit detected-baseline decision and same-process multi-dataset reuse still work;
- readiness-gate and experimental baseline-separation regressions remain green.

Validation for this RC5 package:

- `pytest`: 1,289 passed, 3 skipped, 5 subtests passed;
- `unittest` with the release component directories on `PYTHONPATH`: 416 passed, 1 skipped.

This build remains a release candidate and is not yet the final study freeze.
