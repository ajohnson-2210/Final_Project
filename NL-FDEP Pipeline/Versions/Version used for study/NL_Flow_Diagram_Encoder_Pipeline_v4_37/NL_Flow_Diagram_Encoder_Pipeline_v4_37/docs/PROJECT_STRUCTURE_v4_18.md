# NL-FDEP v4.18 project structure

AJ Dialect v1.4 is unchanged. The grouped project layout is retained.

## Root

- `pycharm_runner.py` — visible interactive entry point
- `README.md`
- `requirements.txt`
- `VERSION`
- `pytest.ini`

Implementation remains grouped under `flow diagram components/`, `parser components/`, `compiler components/`, `pipeline components/`, `study components/`, and `cli components/`. Examples, documentation, manifests and tests remain under their existing folders.

## Batch-level study analysis history

The latest analysis remains under `study_analysis/`, and every invocation is preserved under:

```text
study_analysis/
├── batch_report.json
├── batch_report.csv
├── algorithm_scores.json
├── algorithm_scores.csv
├── criterion_evidence.csv
├── review_queue.csv
├── flowchart_impact.csv
├── human_review_status.csv
├── study_preflight.json
├── study_preflight.csv
├── latest_run.json
└── run_history/
    └── <batch_run_id>/
        ├── ...analysis snapshot files...
        └── run_metadata.json
```

## Per-algorithm rerun history

When an algorithm is genuinely reprocessed, the previous current-view artefacts are moved aside first:

```text
Algorithm - n/
└── pipeline_artifacts/
    ├── manifest.json                 # current run
    ├── pipeline_report.json          # current run
    ├── ...current run artefacts...
    ├── scoring/
    │   └── ...current scoring artefacts...
    └── run_history/
        └── <previous_run_id>/
            ├── manifest.json
            ├── pipeline_report.json
            ├── ...previous run artefacts...
            ├── scoring/
            └── archive_metadata.json
```

This keeps the normal current-run paths stable while preventing stale files from contaminating later runs.
