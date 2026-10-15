# NL-FDEP v4.35 Release Candidate 7

v4.35 RC7 retains the RC6 scoring semantics, Common Tests v1.3, test-spec schema v1.4, AJ_24038155 Dialect v1.5, frozen model-neutral semantic evaluation, session-scoped baseline lifecycle, and baseline isolation from experimental scoring.

RC7 changes only the **baseline readiness user experience** for the narrow case where calibration completes with exactly 49 of 50 algorithms fully evaluated at 100% and the remaining algorithm is unavailable because calibration could not be completed.

## Normal readiness remains 50/50

The normal experimental readiness gate is unchanged:

- 50/50 terminal baseline calibration runs;
- 50/50 behaviourally evaluated calibrations;
- 50/50 calibration scores at 100%.

A baseline with an evaluated score below 100% is **not** eligible for the degraded override. RC7 does not weaken or reinterpret behavioural disagreement as an environmental exception.

## Explicit degraded 49/50 override

If calibration ends with exactly:

- 50/50 terminal outcomes;
- 49/50 behaviourally evaluated calibrations;
- 49/50 calibration scores at 100%;
- exactly one unavailable calibration;

RC7 displays the unavailable algorithm and the best available failure reason, then asks whether the user wants to continue with the 49 fully calibrated algorithms.

If the user selects **No**, the LLM operation does not start.

If the user selects **Yes**, the current process is marked:

```text
DEGRADED_49_OF_50_OVERRIDE
```

The override is session-only. It is never written as a persistent study-ready state and is never supplied to experimental semantic scoring.

A typical dependency failure is surfaced directly, for example:

```text
Algorithm 50: PIPELINE_FAILURE
Reason: ModuleNotFoundError: No module named 'matplotlib'
```

This allows the user either to install/fix the missing dependency and recalibrate, or to explicitly accept the 49/50 procedural gate for that process.

## Session integrity

The accepted degraded state records the unavailable algorithm ID in memory. Before every LLM batch, the runner rechecks the baseline. The session is allowed to continue only if:

- the baseline becomes fully 50/50 ready; or
- it still exactly matches the explicitly accepted 49/50 degraded state.

If another calibration changes, fails, disappears, or the unavailable algorithm changes, the override is invalidated and the next LLM batch is blocked.

The console header now reports either:

```text
Baseline readiness: FULL_50_OF_50
```

or:

```text
Baseline readiness: DEGRADED_49_OF_50_OVERRIDE (unavailable: Algorithm n; explicit session-only acceptance)
```

## Failure diagnostics

For non-ready calibration states, RC7 now includes individual calibration problem details where available. Reasons are sourced from the current batch report and pipeline/calibration artefacts, rather than presenting only aggregate 49/50 or 50/50 counts.

## Unchanged study methodology

RC7 does **not** change:

- Common Tests v1.3;
- semantic behavioural scoring;
- experimental expected values;
- baseline isolation from experimental scoring;
- automated/human rubric streams;
- the 50:50 automated/human combined rubric method;
- pseudocode parsing, flow generation or Python generation.

The degraded override affects only whether the user may explicitly continue a session after one unavailable baseline calibration.

## RC7 regression coverage

RC7 adds tests proving that:

- exactly 49/50 fully calibrated plus one unavailable algorithm is eligible for explicit override;
- the popup contains the unavailable algorithm and its failure reason;
- declining the override blocks the experimental operation;
- an evaluated calibration below 100% cannot use the override;
- an accepted override is invalidated if the degraded state changes;
- existing strict 50/50 readiness and session-state regressions remain green.

Validation for this RC7 package:

- `pytest`: 1,298 passed, 3 skipped, 5 subtests passed;
- `unittest` with all release component directories on `PYTHONPATH`: 425 passed, 1 skipped.

This build remains a release candidate and is not yet the final study freeze.
