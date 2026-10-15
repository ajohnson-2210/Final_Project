# NL-FDEP v4.36 release

NL-FDEP v4.36 supersedes the neutral v4.35 package. It deliberately preserves the v4.35 transformation, baseline-readiness, Human Review, Semantic Boundary Variance, rubric, dashboard and dependency-management behaviour. The active study instrument remains Common Tests v1.4.2 / test-spec schema v1.6 with 50 suites and 156 declared cases (129 `CORE_BEHAVIOURAL`, 8 `PRE_FREEZE_VALIDATION`, 19 `SEMANTIC_BOUNDARY_PROBE`).

## Version change

- Runtime pipeline version is `4.36`.
- Release folder/package naming uses `NL_Flow_Diagram_Encoder_Pipeline_v4_36`.
- Scoring Rubric remains v1.1 and scoring schema remains 1.5.
- AJ dialect remains `AJ_24038155_DIALECT_V1.5`.
- Common Tests v1.4.2 are unchanged from the final v4.35 package.

## Examples-folder conformance refresh

The `examples/` folder was audited against the current build rather than carried forward as historical sample output.

- `example.aj` was rerun through `AJ_DIALECT_STRICT` and completes parsing, flow encoding, DrawIO export and Python compilation.
- `example_ast.json`, `example_report.json`, `ast_visualisation.html`, flow-diagram artefacts and generated Python were regenerated from that source.
- `example_pipeline_report.json` and `example_compilation_report.json` use portable example-relative paths instead of build-machine paths.
- The parser-only `sum_even` artefacts (`ast_output.json`, `parser_report.json`, `pycharm_example_output.txt`) were regenerated with the current parser and now identify v4.36 / AJ Dialect v1.5 rather than the historical Dialect v1.0 parser.
- `tic_tac_toe.drawio` was verified against the current DrawIO input route.
- `study_tests_template.json` now demonstrates test-spec schema 1.6 / design 1.4.2, `STATIC_PREEXPERIMENT_EXPECTATIONS`, a frozen semantic contract, explicit score streams and `runtime_oracle_prohibited: true`.
- `examples/README.md` documents the role and provenance of each example family.

## Human Review usability refinement

The authoritative HTML questionnaire has been streamlined for faster repeated review without changing the saved review schema or scoring methodology.

- **Source Sufficiency → Reviewer Justification** now uses a preset response selector with **Other — add specific comment** revealing a textarea.
- **Behavioural Evidence Adequacy → Reviewer Evidence Comment** uses the same selector/Other pattern.
- **Task-Semantic Evaluation → Reviewer Semantic Justification** uses the same selector/Other pattern.
- Existing free-text responses remain backward-compatible: when a saved response does not match a preset, the questionnaire resumes it under **Other** with the previous text restored.
- Major questionnaire headings now use title case, including **Source Sufficiency**, **Behavioural Evidence Adequacy**, **Task-Semantic Evaluation**, **Stage Criteria** and **Overall Review**.
- The questionnaire uses restrained blue section styling, clearer criterion cards, focus states and button styling to improve scanability.
- The underlying JSON fields remain unchanged; this is a presentation/input-efficiency change only.

## Preserved study controls

- Baseline algorithms are excluded from Human Review.
- Baseline readiness requires pipeline success for 50/50 algorithms and 100% for every behaviourally evaluable calibration; genuine `BEHAVIOURAL_NOT_EVALUATED` remains separate.
- Baseline activation remains session-scoped and is not silently restored across normal restarts.
- Experimental expected values remain static and pre-experiment; the baseline is never a runtime scoring oracle.
- Semantic Boundary Variance remains separate from core behavioural scoring.
- Automated and human rubric streams remain separate; combined rubric scoring is produced only under the established full-review rules.
- The HTML questionnaire remains the authoritative Human Review interface with study-wide reviewer ID/name ownership protection.
- Automatic dependency verification/installation and automatic dashboard generation are retained.

## Common Test provenance

Common Tests v1.3, v1.4 and v1.4.1 remain historical frozen packs. Common Tests v1.4.2 remains the active pack and is unchanged by the v4.36 version/examples refresh.
