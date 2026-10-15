# NL-FDEP v4.08 — Experimental infrastructure freeze

v4.08 freezes the experimental infrastructure around the AJ_24038155 Dialect v1.2 pipeline. It does **not** add AJ syntax or broaden compiler semantics.

## Added

- Automatic study pre-flight validation (`study_preflight.json` and `.csv`) for Algorithms 1–50.
- SHA-256 provenance for source pseudocode, reference Python, test specifications and the frozen rubric.
- Per-run IDs and start/completion timestamps in `manifest.json`.
- Resume support for unchanged runs and protection of completed human reviews from silent overwrite.
- `--force` reprocessing with archival of existing human review/final-score artefacts.
- Independent baseline-reference validation using researcher-specified expected outcomes. Tests whose expected values are derived from reference Python are explicitly excluded from validating that same reference.
- `baseline_reference_validation.json`.
- Paired direct-AST versus flow-mediated compilation/testing in `flow_mediation_analysis.json`, including direct control artefacts (`direct_ast_program.py`, compilation report and test report when applicable).
- A clear distinction between the descriptive AST-vs-flow rubric score difference and the behavioural `flow_mediation_delta`.
- Integrated human-review dashboard that writes `human_review.json` directly into the algorithm scoring directory and immediately adjudicates `final_score.json`.
- Baseline-specific human-review question asking whether the supplied reference Python is an appropriate implementation.
- Analysis CSV fields for flow mediation and baseline-reference validation.

## Interpretation boundary

`flow_mediation_delta` compares the direct AST-structured compilation path with the ordinary flow-structured compilation path under the same behavioural tests. It measures the effect of the machine-readable intermediate representation used by NL-FDEP. It does not establish how an LLM or human would perform when shown a rendered flowchart image instead of pseudocode.

## Run safety

A current completed run is skipped by default. A reviewed run whose inputs change is marked `REVIEW_PROTECTED_INPUT_CHANGED` and is not overwritten. Explicit forced reprocessing archives the previous `human_review.json` and `final_score.json` before generating replacements.

## Language/compiler scope

No AJ_24038155 Dialect v1.2 language rule is changed by v4.08. Parser, normalisation and Python-lowering semantics remain those of the audited v4.07 core.

## Validation

- 1,157 pytest tests passed; 3 skipped; 5 subtests passed.
- 344 unittest tests passed; 1 skipped.

