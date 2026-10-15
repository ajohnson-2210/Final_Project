# NL-FDEP v4.35 RC14

## Direct cross-session Human Review study detection

RC14 changes only Human Review discovery/UX. Pipeline transformation semantics, Common Tests v1.4.1, Semantic Boundary Variance, baseline calibration, rubric scoring, dashboard methodology, and RC13 dependency/bootstrap behaviour are unchanged.

### Detect previous study no longer requires a folder chooser

When a completed experimental LLM batch is processed, NL-FDEP now remembers only the parent study directory used for Human Review discovery. This harmless pointer is stored separately from the baseline crash-recovery state and contains no baseline activation, calibration state, score, or human-review answer.

On a later runner launch, choosing **Human review folder → Detect previous study** uses that remembered study directory to rebuild the AI-agent selector directly from completed experimental Human Review artefacts already on disk. If valid reviewable datasets are found, the Human Review window opens immediately and the folder chooser is not displayed.

Baseline questionnaires remain excluded from discovery.

### Start fresh remains explicit

Choosing **Start fresh** still opens the LLM-folder chooser and loads only the explicitly selected experimental dataset. Additional datasets can still be added from the Human Review window with **Add LLM dataset**.

If no previous study pointer exists, or the remembered location no longer contains reviewable experimental datasets, NL-FDEP explains that no previous study was detected and falls back to a one-time folder selection so a new discovery location can be established.

### Safety separation

The Human Review discovery pointer is intentionally independent of `runner_state.json`. RC13's baseline session-safety behaviour is unchanged: an orderly runner exit clears the baseline recovery hint and no baseline is silently activated across sessions.

### Regression coverage

RC14 adds regression coverage that verifies:

- a remembered study rebuilds all completed experimental sibling datasets;
- baseline review artefacts are excluded;
- Detect previous study bypasses the folder chooser when the remembered study is valid; and
- existing RC11/RC12 Human Review discovery/start-fresh behaviour remains intact.

### Validation

- `pytest`: 1,324 passed, 3 skipped, 5 subtests passed.
- `unittest` with project component paths: 451 passed, 1 skipped.
- Common Tests v1.3, v1.4, and v1.4.1 are unchanged from RC13.
