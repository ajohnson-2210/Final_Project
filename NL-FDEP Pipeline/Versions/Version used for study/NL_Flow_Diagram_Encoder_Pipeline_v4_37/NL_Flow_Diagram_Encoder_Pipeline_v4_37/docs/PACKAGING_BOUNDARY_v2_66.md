# Packaging boundary — v2.66

The six-model pseudocode corpus is research/study data and is **not part of the parser implementation deliverable**.

## Distribution rule

Versioned implementation ZIPs must exclude:

- `corpus_hash_format/`
- copied/raw model-response corpus files

The corpus may still be used externally during the study audit and regression evaluation.

## External integration-test rule

Study-level corpus tests use the environment variable:

`AJ_RESEARCH_CORPUS_DIR`

When that variable is absent, corpus-dependent integration checks skip cleanly. Unit/regression tests that do not require study data continue to run normally.

This separation prevents the research sample from being distributed as though it were implementation data while preserving reproducible external evaluation.
