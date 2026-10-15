# NL-FDEP v4.37 release

NL-FDEP v4.37 supersedes v4.36 and formally packages the routing and Human Review reliability refinements developed after the v4.36 release package. The frozen study instrument and scoring methodology are unchanged: Common Tests v1.4.2 / test-spec schema v1.6 remains active with 50 suites and 156 declared cases (129 `CORE_BEHAVIOURAL`, 8 `PRE_FREEZE_VALIDATION`, 19 `SEMANTIC_BOUNDARY_PROBE`). AJ_24038155 Dialect v1.5, Scoring Rubric v1.1, scoring schema v1.5, baseline-readiness rules, Semantic Boundary Variance, and baseline-independent experimental scoring are preserved.

## Version change

- Runtime pipeline version is `4.37`.
- Release folder/package naming is `NL_Flow_Diagram_Encoder_Pipeline_v4_37`.
- DrawIO layout revision advances to `v4.37-layout-20260922-1` so earlier v4.37/v4.36 layouts are recognised as stale and refreshed.
- Historical v4.36 release, validation and checksum records remain packaged unchanged for provenance.

## Flow-diagram routing refinements

- Rhombus/decision connectors use true vertices before fractional edge positions.
- Yes/No branches receive first priority on decision vertices; remaining unused vertices are then available to Repeat, continuation, incoming and other logical attachments.
- Rectangular/process-style shapes use the four edge midpoints before any fractional edge positions are introduced.
- Equivalent shared Repeat paths continue to count as one logical attachment where they share a return trunk.
- When primary-anchor rules leave more than one valid unused side, routing is crossing-aware: an unused primary anchor that produces fewer connector crossings is preferred. This is a tie-breaker within the primary-anchor tier and does not justify early fractional placement.
- Algorithm 27-style loop routing therefore avoids the former Repeat/Yes crossing by selecting the clear process midpoint when available.
- Loop-exit paths are explicitly labelled `No`, matching the existing visible `Yes` label, while ordinary sequential `NEXT` connectors remain unlabelled.
- Connection sides now prioritise the primary anchor that physically faces the connected node when available. Horizontal peers therefore prefer right-to-left or left-to-right attachment, while vertically aligned/overlapping peers prefer bottom-to-top or top-to-bottom attachment. Decision Yes/No branch ownership and shared Repeat trunks remain higher-order semantic constraints, and crossing avoidance remains active.

## Comment handling in flow diagrams

`COMMENT` statements remain preserved in the structured AST/source provenance but are no longer encoded as executable flow nodes or edges. This prevents explanatory comments from changing flow-node counts, graph topology, or automated flow-stage results. Existing artefacts that still contain legacy `COMMENT` flow nodes are treated as stale for semantic resume and only those affected algorithms are regenerated; comment-free current baselines continue to use the fast resume path.

## Resume-time DrawIO refresh

Stale experimental DrawIO refresh now occurs before resume-state classification. Protected or otherwise non-regenerated semantic study states can therefore receive the current visual layout without rewriting their semantic artefacts, scores or Human Review data.

## Human Review save-service resilience

- After at least one questionnaire is opened, closing the **NL-FDEP Human Review** launcher with the window-manager X minimises the launcher instead of stopping its local-only `127.0.0.1` save service.
- **End Review Session** is the explicit shutdown path and warns when open questionnaire tabs may still depend on direct saving.
- If the local service is genuinely unreachable, **Save review** downloads a backup `human_review.json` so completed review input is not lost.
- HTTP save errors continue to report server-provided errors and do not silently overwrite reviewer ownership protections.

## Reviewer identity auto-population correction

The v4.36 failed-fetch fallback message could be emitted into the generated questionnaire JavaScript with invalid quoting. In affected rendered pages, that syntax error prevented the questionnaire initialisation routine from running, which also prevented Reviewer ID and Reviewer Name from appearing even though the identity data had been supplied correctly.

v4.37 generates the fallback message with JSON-safe JavaScript embedding. The rendered script parses correctly, and the selected Reviewer ID/name pair is populated automatically in the questionnaire as intended. Existing reviewer-ID/name association and cross-reviewer overwrite protections are unchanged.


## Baseline resume compatibility

v4.37 does not recalibrate an already-current v4.36 baseline merely because the package version changed. v4.36 baseline artefacts are accepted for resume only when their source pseudocode, reference Python, Common Tests, rubric, dependency environment and strict baseline profile still match **and** their canonical flow graph does not contain a legacy `COMMENT` node. Comment-free baselines therefore retain the fast baseline-start behaviour, while only algorithms affected by the comment-as-flow-node defect are regenerated. Parser/compiler behaviour and the frozen study methodology remain unchanged.

The v4.37 compatibility check is **version-specific for rubric provenance**. Scoring Rubric v1.1 embeds the pipeline version in its rubric document, so an otherwise identical v4.36 rubric has SHA-256 `72c285d390630dc4e1d341537de06f025b4a49b4eb023f94215f70ee0d6dfb72`, while the v4.37 document has a different hash. The initial v4.37 compatibility implementation still compared legacy manifests to the v4.37 rubric hash, causing genuine v4.36 baselines to be misclassified as stale and silently recalibrated. The corrected implementation validates each compatible manifest against the rubric hash belonging to that pipeline version. A 50-algorithm baseline produced by the working v4.36 processor is now resumed as 50/50 `SKIPPED_CURRENT` rather than reprocessed.

## Comparative radial dashboard centre statistic

The centre of `NL-FDEP Comparative Radial Dashboard.html` now reports the data-derived **highest mean behavioural score** across the available AI agents and names the agent holding that maximum. The value is calculated from the rendered study data and is not hard-coded to any specific model or vendor. If multiple agents share the exact maximum, the centre reports a joint-highest result rather than implying a unique winner. Sidebar and radial-sector selections continue to update the selected model summary independently; the centre remains a stable study-level benchmark callout.

## Comparative dashboard filename authority

`<study-root>/analysis/dashboards/NL_FDEP_comparative_dashboard.html` is the sole generated study-level comparative heat-map dashboard. The duplicate `NL_FDEP_interactive_heatmap_dashboard_v5.html` output is no longer written. The existing `interactive_heatmap_dashboard` status key is retained for caller compatibility, but it resolves to the canonical `NL_FDEP_comparative_dashboard.html` path rather than to a second physical HTML file.

## Preserved study controls

- Baseline algorithms remain excluded from Human Review.
- Baseline readiness remains 50/50 pipeline success plus 100% across every behaviourally evaluable calibration.
- Genuine `BEHAVIOURAL_NOT_EVALUATED` remains separate from pipeline readiness.
- Baseline activation remains session-scoped and is never silently restored across ordinary restarts.
- Experimental expected values remain static and pre-experiment; the baseline is not a runtime scoring oracle.
- Semantic Boundary Variance remains descriptive and separate from core behavioural and rubric scoring.
- Automated and human rubric streams remain separate; combined rubric scoring follows the established complete-review rule.
- Common Tests v1.3, v1.4 and v1.4.1 remain historical frozen packs; v1.4.2 remains the active unchanged pack.

## Validation

The release is validated with the complete pytest and unittest suites, targeted comment-exclusion and peer-facing-anchor regressions, Algorithm 27 crossing-aware routing checks, shared Repeat-trunk checks, DrawIO stale-refresh regression checks, Human Review local-save/fallback/identity tests, rendered questionnaire JavaScript syntax validation, checksum verification and ZIP integrity validation. Exact counts are recorded in `docs/v4_37_validation.json`.

## Presentation-ready example runs

The `examples/` directory is organised as two reproducible, single-input demonstrations intended for inspection and video presentation rather than batch study execution.

- The parent `examples/` artefacts are generated by a real `NLFlowDiagramEncoderPipeline` pseudocode-input run. The demonstration source includes input, conversion, a decision, a loop and output, and its four local behavioural cases all pass.
- `examples/tic_tac_toe/` is generated by the real `DrawIOFlowInputPipeline` using `tic_tac_toe.drawio` as the input. The imported graph contains 35 shapes and 50 connectors, compiles to structured Python, generates a Python AST, and passes two local behavioural demonstrations covering a Player 1 win and a draw.
- These demonstration cases are not part of the frozen Common Tests and do not alter study scoring or methodology.
- Each example includes a reproduction script and a generated `run_summary.txt`; report paths are normalised to project-relative paths only for release portability.

## Legacy example cleanup

The presentation `examples/` directory contains only the current reproducible pseudocode-input run plus the `examples/tic_tac_toe/` Draw.io-input run. Retired mixed-example artefacts from earlier releases are not packaged: `example.aj`, the old `example_*` outputs, `ast_output.json`, `pycharm_example_output.txt`, the former root-level `tic_tac_toe.drawio`, and `examples/study_tests_template.json`. The current `parser_report.json` and `ast_visualisation.html` are generated by the current presentation pseudocode run and are retained intentionally.
