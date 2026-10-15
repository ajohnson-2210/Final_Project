# NL-FDEP v4.35 RC12

## Cross-session Human Review discovery and fresh-start control

RC12 extends the RC11 questionnaire-driven Human Review workflow without changing pipeline transformation, Common Tests v1.4.1, calibration, Semantic Boundary Variance, rubric scoring, or dashboard methodology.

### Standalone Human Review startup choice

After choosing **Human review folder**, the runner now offers:

- **Resume / discover existing study** — select any completed experimental LLM dataset (outer folder or `Results`). NL-FDEP scans the selected dataset's immediate study parent for sibling completed LLM datasets that contain valid human-review questionnaires. Baseline datasets are excluded.
- **Start fresh** — only the explicitly selected LLM dataset is loaded. No sibling discovery is performed.

The runner prints the startup mode and, in discovery mode, the number of completed experimental LLM datasets reconstructed. No persistent review-session registry is written.

### Add LLM dataset

The Human Review window now includes **Add LLM dataset**. It adds only the explicitly selected dataset, de-duplicates existing entries, excludes baseline datasets, and updates the dataset selector immediately. This allows a fresh review session to be expanded deliberately without rebuilding the whole study list.

### Same-session behaviour preserved

When multiple LLM folders are processed before Human Evaluation in one uninterrupted runner session, the existing in-memory registry is still used directly. Cross-session sibling discovery is not invoked in that path.

### Preserved controls

- Baseline algorithms never enter Human Review.
- Algorithm ordering remains numeric 1 through 50.
- Human Review remains questionnaire-driven and saves to `human_review.json`.
- Common Tests v1.4.1 is unchanged.
