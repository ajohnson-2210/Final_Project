# NL-FDEP v4.17 project structure

The grouped v4.16 project structure is retained. AJ Dialect v1.4 is unchanged.

## Root

- `pycharm_runner.py` — visible interactive entry point
- `README.md`
- `requirements.txt`
- `VERSION`
- `pytest.ini`

Implementation files remain grouped under the existing component folders, with manifests under `manifests/`, examples under `examples/`, documentation under `docs/`, and tests under `tests/`.

## Study analysis output

A processed dataset keeps the latest analysis at:

```text
study_analysis/
├── study_preflight.json
├── study_preflight.csv
├── batch_report.json
├── batch_report.csv
├── algorithm_scores.json
├── algorithm_scores.csv
├── criterion_evidence.csv
├── review_queue.csv
├── flowchart_impact.csv
├── human_review_status.csv
├── latest_run.json
└── run_history/
    └── <batch_run_id>/
        ├── study_preflight.json
        ├── study_preflight.csv
        ├── batch_report.json
        ├── batch_report.csv
        ├── algorithm_scores.json
        ├── algorithm_scores.csv
        ├── criterion_evidence.csv
        ├── review_queue.csv
        ├── flowchart_impact.csv
        ├── human_review_status.csv
        └── run_metadata.json
```

The top-level files are the latest convenient view; the run-history copies preserve previous batch evidence.
