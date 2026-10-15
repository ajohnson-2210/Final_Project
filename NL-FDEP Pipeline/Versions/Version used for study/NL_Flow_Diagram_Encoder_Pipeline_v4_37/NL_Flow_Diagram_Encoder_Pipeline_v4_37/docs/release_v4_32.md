# NL-FDEP v4.32 release note

Pipeline: **NL-FDEP v4.32**  
Language: **AJ_24038155 Dialect v1.5**  
Baseline profile: **AJ_DIALECT_STRICT**  
Experimental profile: user-selectable, including **GENERIC_COMPATIBILITY**  
Common Tests: **v1.1 — 50 suites / 113 executable tests**  
Scoring Rubric: **v1.1**  
Scoring Schema: **v1.4**

## Purpose

v4.32 incorporates the LLM-results-folder runner correction into a normal versioned release. Apart from that orchestration correction and the pipeline version identifier, v4.32 is the same implementation as v4.31.

## Corrected LLM results workflow

The v4.31 interactive runner could allow the Baseline benchmark directory selected during dependency setup to be reused as the subsequent `LLM_RESULTS_FOLDER` input. In that state the study batch processed the Baseline directory as though it were the experimental dataset, typically producing `Algorithms represented: 0`.

v4.32 makes the hand-off explicit:

1. Select `LLM_RESULTS_FOLDER`.
2. Select the experimental pseudocode profile.
3. If no baseline dependency is supplied, the runner asks whether one should be provided.
4. Select the Baseline benchmark folder.
5. The baseline is preflight-checked and, when required, calibrated under v4.32 Strict mode.
6. The runner displays **Baseline benchmark ready**.
7. The runner then explicitly asks for the experimental LLM results dataset.
8. The Baseline folder is rejected if selected as the LLM dataset.
9. The selected LLM folder is processed against the supplied baseline.

## Accepted LLM folder layouts

The LLM selector accepts either of these layouts:

```text
LLM root/
  Algorithm - 1/
    Algorithm 1 Pseudocode.txt
  ...
  Algorithm - 50/
    Algorithm 50 Pseudocode.txt
```

or:

```text
LLM root/
  results/
    Algorithm - 1/
      Algorithm 1 Pseudocode.txt
    ...
    Algorithm - 50/
      Algorithm 50 Pseudocode.txt
```

When the parent form is selected, v4.32 automatically resolves the single `results` child containing the Algorithm folders.

## What did not change

There is no change to:

- AJ_24038155 Dialect v1.5 syntax or semantics;
- parser or AST semantics;
- flow-diagram semantics;
- Python compiler/lowering semantics;
- Common Tests v1.1;
- behavioural oracle construction;
- scoring rubric or scoring schema;
- baseline Strict-profile requirement; or
- experimental pseudocode-profile selection.

## Baseline currentness

NL-FDEP calibration manifests include the pipeline version as a currentness field. Therefore a calibration produced by v4.31 is intentionally stale under v4.32. Select the same frozen 100% baseline and allow v4.32 to recalibrate it once. Since the transformation/testing semantics are unchanged, the expected calibration result remains 50/50 algorithms evaluated at 100%. After that v4.32 calibration exists, subsequent LLM runs can reuse it while it remains current.

This preserves the study's version-provenance rule rather than silently treating artefacts from two nominal pipeline versions as identical.
