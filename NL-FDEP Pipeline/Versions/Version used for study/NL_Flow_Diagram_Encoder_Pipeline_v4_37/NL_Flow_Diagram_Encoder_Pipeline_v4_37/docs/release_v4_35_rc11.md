# NL-FDEP v4.35 RC11

## Human Review workflow and baseline progress UX

RC11 expands the integrated Human Review workflow while preserving RC10 scoring, Common Tests v1.4.1, baseline calibration rules, Semantic Boundary Variance, and automatic dashboard generation.

### Session-wide LLM human review

- Every experimental LLM results folder processed in the current runner session is retained in an in-memory review registry.
- Choosing Human Evaluation opens one review window with a dataset selector containing all LLM datasets processed in that session.
- Six 50-algorithm datasets therefore provide access to all 300 experimental algorithms in one review session.
- Baseline algorithms are excluded from human review by design.
- The registry remains session-only and is not silently restored after restarting the runner.

### Standalone Human Review folder selection

- Accepts either the outer LLM model folder containing a `Results` child or the `Results` folder itself.
- Baseline `Pseudocode` folders are not accepted as human-review sources.
- Invalid/empty selections show an explicit message rather than an empty algorithm list.

### Numeric algorithm ordering

- Algorithm lists are sorted numerically (`1, 2, ... 50`) rather than lexicographically (`1, 10, ... 2`).

### Questionnaire-driven integrated review

The integrated Tk review interface now uses `human_review_questionnaire.json`, the authoritative structured source from which `human_review_questionnaire.html` is generated. It exposes the same substantive review areas as the verbose HTML questionnaire:

- reviewer ID and confidence;
- G1 source sufficiency, including automated evidence, independent human result, agreement and justification;
- G2 behavioural evidence adequacy, including coverage profile, strengths, limitations, basis and interpretation;
- task-semantic contract and automated semantic evidence plus independent human semantic assessment;
- all sixteen rubric criteria with automated score/status/confidence/justification/evidence and independent 0/1/2/NA human assessment;
- overall semantic-loss/faithfulness observations.

The previous compact-interface shortcuts that automatically copied the automated G1 result, marked agreement as `AGREE`, or defaulted overall review answers have been removed. Human judgements are now entered explicitly.

The interface saves directly to `human_review.json`, re-runs adjudication, and supports resuming an existing saved human review. An **Open full questionnaire HTML** button remains available for viewing the exact portable HTML artefact.

### Baseline progress message

After Common Test pack readiness is printed for a baseline benchmark run, the console now immediately prints and flushes:

`Baseline testing and calibration in progress — evaluating 50 algorithms against Common Tests v1.4.1…`

This is a presentation-only UX improvement; no calibration or scoring logic is changed.

### Preserved methodology

- Common Tests v1.4.1 remains unchanged from RC10.
- 129 `CORE_BEHAVIOURAL`, 8 `PRE_FREEZE_VALIDATION`, and 19 `SEMANTIC_BOUNDARY_PROBE` cases remain unchanged.
- Algorithm 22 remains `NON_NEGATIVE_INTEGER` with `0! = 1` as a core behavioural case.
- Baseline algorithms do not require human review.
- Combined Rubric Score remains available only after all sixteen human rubric criteria are explicitly completed.
