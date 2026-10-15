# NL-FDEP v4.35 RC9

RC9 adds automatic, downstream dashboard generation after study batch completion while retaining RC8 Common Tests v1.4 / Semantic Boundary Variance, RC7 degraded baseline readiness handling, and RC6 rubric semantics.

## Automatic dashboard generation

After the structured batch reports and aggregate analysis files are finalised, the pipeline now generates a self-contained HTML presentation layer automatically.

### Per-batch dashboard

Every completed baseline or LLM batch writes:

`study_analysis/dashboards/NL_FDEP_batch_dashboard.html`

For LLM datasets the dashboard includes all 50 algorithm positions, behavioural scores, reference comparison, pipeline outcome, Semantic Boundary Variance, automated/human/combined rubric fields when available, transformation-stage scores, behavioural evidence notes, assessed pseudocode, generated Python, and local-file-safe Copy buttons.

The established behavioural colour scale is retained:

- 0: `#2f6db3`
- 25: `#6ec5ff`
- 50: `#ffc145`
- 75: `#9be564`
- 100: `#2ca25f`
- white: not evaluable / no behavioural score

### Comparative study dashboard

After an LLM batch completes, RC9 scans sibling study folders case-insensitively for completed `Results`/`results` datasets and regenerates:

`<study-root>/analysis/dashboards/NL_FDEP_comparative_dashboard.html`

The comparative dashboard shows every completed experimental AI agent across all 50 algorithms and ranks agents using the agreed **Combined Behavioural Measure**:

`(Mean Experimental Semantic Behavioural Score + Aggregate Task-Semantic Common Test Accuracy) / 2`

Semantic Boundary Variance and available Combined Rubric evidence are shown separately; neither is silently folded into the Combined Behavioural Measure.

Baseline calibration is never included as an experimental comparison row.

## Scientific isolation and failure handling

Dashboard generation happens only after scoring/analysis artefacts are written. It does not participate in:

- baseline calibration;
- Common Test expected-value generation;
- semantic behavioural scoring;
- Semantic Boundary Variance classification;
- automated rubric scoring;
- human rubric scoring or adjudication.

A dashboard-generation failure is non-fatal. `study_analysis/dashboard_generation.json` records `FAILED` plus the error, while the completed scientific batch remains authoritative and usable.

Successful dashboard outputs and the dashboard status file are included in each batch-level `run_history` snapshot.

## Runner output

The PyCharm runner now prints dashboard-generation status and the generated batch/comparative dashboard paths after `STUDY BATCH COMPLETE`.

## Validation

- automatic-dashboard targeted tests: PASS
- study/baseline/rubric/SBV regression subset: PASS
- full pytest: 1307 passed, 3 skipped, 5 subtests passed
- full unittest: 434 passed, 1 skipped
- generated batch/comparative dashboard JavaScript syntax validation: PASS
