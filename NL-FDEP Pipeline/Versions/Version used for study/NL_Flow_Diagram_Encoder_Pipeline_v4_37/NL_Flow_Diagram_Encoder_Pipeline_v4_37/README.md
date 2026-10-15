# NL Flow Diagram Encoder Pipeline v4.37

## v4.37 release — current study build

NL-FDEP v4.37 supersedes v4.36 while preserving the frozen Common Tests v1.4.2 / test-spec schema v1.6 study instrument, AJ_24038155 Dialect v1.5, Scoring Rubric v1.1, scoring schema v1.5, baseline-readiness rules, Semantic Boundary Variance methodology, and baseline-independent experimental scoring.

v4.37 promotes the post-v4.36 reliability and diagram-routing refinements into a documented release. Flow diagrams now exhaust true decision vertices and process-shape midpoints before fractional edge attachments, prioritise Yes/No decision branches on vertices, prefer primary connection sides that physically face the connected node, use crossing-aware primary-side selection when an unused primary anchor reduces connector crossings, and explicitly label loop exits as **No**. Non-executable `COMMENT` statements remain in source/AST provenance but are excluded from flow nodes and edges so comments cannot distort topology or automated flow-stage results. Stale experimental DrawIO outputs are refreshed before resume classification so protected study states do not retain an older layout revision.

Human Review is hardened against local save-service loss: closing the launcher after questionnaires have been opened minimises it rather than silently stopping the service; **End Review Session** is the deliberate shutdown path; an unreachable local save service triggers a backup `human_review.json` download; and the rendered questionnaire JavaScript now uses JSON-safe status-message generation so Reviewer ID and Reviewer Name populate automatically and remain available as intended.

See `docs/release_v4_37.md` for the complete release record. The v4.36 release record remains available at `docs/release_v4_36.md`.

### v4.35 RC14 direct previous-study Human Review discovery

RC14 keeps Common Tests v1.4.1 and all scoring/calibration methodology unchanged while improving cross-session Human Review. Completed experimental LLM processing now remembers a separate, non-scoring Human Review study pointer. On a later launch, **Human review folder → Detect previous study** rebuilds the AI-agent selector from completed experimental artefacts and opens Human Review directly without asking the user to choose an anchor folder again. Baseline datasets remain excluded.

**Start fresh** still asks for one LLM dataset and does not rebuild the previous study list. The Human Review pointer is independent of baseline `runner_state.json`, so RC13's no-silent-baseline-activation safety rule remains unchanged. See `docs/release_v4_35_rc14.md`.

### v4.35 RC13 baseline-session and dependency bootstrap

RC13 keeps Common Tests v1.4.1 and all scoring methodology unchanged while improving the runner workflow. Before Baseline or LLM study processing, the runner verifies the active Python environment against `requirements.txt` and then `requirements-optional.txt`. If packages are missing, the user can install them into the exact interpreter running NL-FDEP; the two requirement files are processed in that order.

A completed standalone Baseline benchmark run no longer terminates the process. When the baseline satisfies readiness, it remains active in memory and the main options menu is shown again. Selecting an LLM results folder in the same process reuses that baseline directly without another baseline-selection prompt. Orderly process exit still clears the external recovery hint, so there is no silent cross-session baseline activation.

RC13 removes the historical `DEGRADED_49_OF_50_OVERRIDE`. Study readiness now requires **50/50 pipeline-successful baseline algorithms** and **100% for every behaviourally evaluable calibration**. A frozen behavioural case that is genuinely `BEHAVIOURAL_NOT_EVALUATED` remains explicitly reported and does not create a degraded baseline state. See `docs/release_v4_35_rc13.md`.

### v4.35 RC10 pre-freeze validation correction

RC10 corrects the baseline-calibration regression introduced by RC8 and inherited by RC9. Eight newly proposed valid-domain edge cases for Algorithms 12, 44, 45 and 46 had been promoted directly into `CORE_BEHAVIOURAL` before being validated against the established baseline. They are retained, not deleted, but moved to `PRE_FREEZE_VALIDATION`. These cases may be executed and reported descriptively, but they do not affect baseline calibration, pipeline SUCCESS/FAILURE, experimental Common Test accuracy, semantic behavioural scoring, rubric scoring, or Semantic Boundary Variance.

The core calibration/scoring surface for Algorithms 12, 44, 45 and 46 is therefore restored to the three previously frozen cases from Common Tests v1.3 until the candidate edge cases pass explicit baseline validation. Algorithm 22 remains `NON_NEGATIVE_INTEGER` with `0! = 1` as a frozen core test. See `docs/release_v4_35_rc10.md` and `study data/common tests v1.4.1/README.md`.

### v4.35 RC8 Common Tests v1.4 and Semantic Boundary Variance

RC8 introduces **Semantic Boundary Variance (SBV)** as a separate descriptive behavioural measure. Core task-semantic tests continue to determine the existing Common Test accuracy and experimental semantic behavioural score. Tests tagged `SEMANTIC_BOUNDARY_PROBE` never enter that denominator. Instead, they measure how often a generated implementation accepts and processes an input that is outside the frozen semantic contract.

`SBV = out-of-domain probes accepted / evaluable semantic-boundary probes × 100`

A high SBV therefore indicates semantic-domain extension, not automatically incorrect core behaviour. Boundary-probe outcomes are retained as `OUT_OF_DOMAIN_ACCEPTED`, `CONTROLLED_REJECTION`, `INCIDENTAL_FAILURE`, or `NOT_EVALUABLE`. The baseline may exercise the same frozen probes during calibration for pre-study validation/context, but baseline behaviour does not redefine the semantic contract and is never used as an experimental runtime oracle.

RC8 also corrects the Common Test audit defects identified during the v1.3 review, including: Algorithm 22 now defines factorial over `NON_NEGATIVE_INTEGER` and explicitly tests `0! = 1`; Algorithm 33 treats zero as a valid non-negative square-root input; Algorithm 20 moves zero/negative divisor inputs out of core scoring into the semantic-boundary stream; Algorithm 40's evidence metadata now correctly records that the frozen queue sequence reaches an empty dequeue. Legacy “not externally injectable” wording has been removed from v1.4.

RC7's normal 50/50 baseline readiness gate and explicit session-only 49/50 unavailable-calibration override are retained unchanged. See `docs/release_v4_35_rc8.md`, `docs/common_tests_v1_4_semantic_boundary_methodology.md`, and `docs/study_scoring_method_v1_2.md`.

### v4.35 RC6 side-by-side rubric combination

RC6 retains RC5's session-scoped baseline readiness gate and the frozen Common Tests v1.3 behavioural workflow. It changes only the final rubric-combination semantics: automated and human C1-P4 scores are retained as two parallel streams, and human scores no longer substitute for automated criterion values.

After all sixteen human rubric criteria have been explicitly completed with `0`, `1`, `2`, or `NA`, the final combined rubric percentage is calculated as:

```text
(Automated Rubric Percentage + Human Rubric Percentage) / 2
```

The automated and human streams therefore each carry 50% weight. Partial human review is retained for agreement/disagreement analysis but does not create a combined rubric score. Scoring schema is **1.5** and the human-review questionnaire schema is **1.3**; the C1-P4 questions and anchors remain Scoring Rubric v1.1.

The experimental behavioural readout remains separate and unchanged. In particular, **Mean experimental semantic behavioural score** and **Aggregate task-semantic test accuracy** are Common Test behavioural metrics and are not averaged with the rubric scores. Analysis exports now expose `AutomatedRubricPercent`, `HumanRubricPercent`, and `CombinedRubricPercent` side by side. See `docs/release_v4_35_rc6.md` and `docs/study_scoring_method_v1_1.md`.

### v4.35 RC5 session-scoped baseline readiness gate

For `LLM_RESULTS_FOLDER`, v4.35 RC5 uses the baseline as a **procedural study-readiness gate** while preserving baseline-independent experimental scoring. On the first LLM operation in a runner process, any `runner_state.json` left by an unfinished or legacy session is treated only as a recovery hint: the runner explicitly offers **Use detected baseline**, **Choose baseline folder and recalibrate**, or **Quit**. If no recovery hint exists, the runner goes directly to the baseline-folder chooser. The LLM dataset chooser opens only after a benchmark satisfies **50/50 behaviourally evaluated calibrations and 50/50 calibration scores at 100%**. A chosen replacement baseline is deliberately recalibrated before the LLM workflow resumes.

The established baseline is retained in memory across all LLM datasets selected during the same live runner session. The external `runner_state.json` is now session-scoped: it is deleted after orderly quit, cancellation, or completion of a non-LLM route. Unexpected termination deliberately leaves the file as a crash-recovery hint for the next launch, where it still requires explicit user acceptance and full revalidation. A standalone Baseline benchmark run no longer persists a baseline for the next launch.

The baseline path is retained only by the interactive runner for readiness verification and to prevent selecting the benchmark itself as the experimental dataset. It is deliberately **not passed to `run_llm_results_folder()` or to experimental semantic scoring**.

For `LLM_RESULTS_FOLDER` runs, each enabled semantic case stores its exact frozen input fixture, an explicit static expected semantic value, a declarative invocation adapter, a declarative result observer, and a comparison rule. The runtime may execute only the submitted/generated program, observe its result, normalise that observation, and compare it with the stored static value. It must not execute a baseline program, reference implementation, or executable oracle to derive an expected value from an experimental input.

The semantic evaluator is algorithm-agnostic: task-specific adapters and observers are data in the frozen test pack rather than `algorithm_id` branches in runtime code. Common representation differences such as return-vs-print observation, documented node-member aliases, derived dimensional arguments, empty/not-found sentinels, and numeric tolerance are handled only when declared by the frozen contract. Unsupported or unsafe mappings remain `NOT_EVALUABLE`.

Baseline calibration remains a separate validation activity whose successful completion gates the start of an experimental run; it is not consulted by experimental expected-value generation or scoring. The existing human-review questionnaire uses the same frozen semantic contract for every algorithm, including automated `NOT_EVALUABLE` cases. v4.35 remains a **release candidate for cross-dataset stress testing** and is not yet the final study freeze. See `docs/release_v4_35_rc6.md`, `docs/study_scoring_method_v1_1.md`, and `docs/common_tests_v1_3_frozen_semantic_methodology.md`.

## v4.34 persisted baseline discovery (historical)

v4.34 added persistence of the last successfully selected baseline path for baseline-dependent operations. RC4 reduced that pointer to an explicit detected candidate rather than silently activating it. RC5 completes the transition by making the external state file session-scoped: orderly exits delete it, while a file left by an unexpected or older session is only a recovery hint that must be explicitly accepted and revalidated. The selected path is never forwarded into experimental semantic scoring. See `docs/release_v4_34.md`, `docs/release_v4_35_rc4.md`, and `docs/release_v4_35_rc5.md`. RC6 retains the RC5 state lifecycle unchanged.

## v4.33 task-semantic experimental evaluation

v4.33 retains **AJ_24038155 Dialect v1.5**, the v4.32 parser/compiler/flow semantics, **Scoring Rubric v1.1**, and the controlled 50-algorithm baseline workflow. It advances the packaged study resources to **Common Tests v1.2 / test-spec schema v1.3**. The 50 suites and 113 historical cases are retained, while every algorithm now carries an explicit task-semantic contract derived from the original task specification. Concrete fixtures are baseline-derived and expected semantic results are defined by the task contract, with the frozen trusted baseline resolving deterministic policy details where the task statement is underspecified.

For LLM result folders, v4.33 no longer uses legacy PROGRAM/stdout execution as the experimental accuracy metric when a v1.2 semantic contract is available. Generic function translations are invoked through explicit typed fixtures and scored on canonical semantic results. Cases that cannot be safely invoked remain `NOT_EVALUABLE` rather than being assigned an artificial zero. Baseline calibration itself remains on the frozen PROGRAM/reference oracle and has been revalidated at **50/50 algorithms, 100.0%** under v4.33. The existing human-review questionnaire is extended in place with the same task-semantic contract and human semantic assessment fields for every algorithm, including `NOT_EVALUABLE` cases. See `docs/release_v4_33.md` and `docs/common_tests_v1_2_semantic_methodology.md`.

## v4.32 LLM-results baseline hand-off correction

v4.32 is behaviourally identical to v4.31 for pseudocode parsing, AST construction, flow diagrams, Python generation, Common Tests and scoring. It incorporates the corrected interactive `pycharm_runner.py` workflow for **LLM_RESULTS_FOLDER** runs: after the required baseline benchmark is provided and validated/calibrated, the runner explicitly asks for the experimental LLM results dataset rather than allowing the Baseline folder to become the experimental input. The LLM selector accepts either a directory that directly contains `Algorithm - 1` ... `Algorithm - 50`, or a parent directory whose `results` child contains those folders. Selecting the Baseline folder as the LLM dataset is rejected and re-prompted.

The active language remains **AJ_24038155 Dialect v1.5** and baseline processing remains **AJ_DIALECT_STRICT**. Scoring Rubric v1.1, Scoring Schema v1.4, and Common Tests v1.1 (50 suites / 113 tests) are unchanged. Because calibration manifests are pipeline-version stamped, a frozen v4.31 baseline must be recalibrated once under v4.32 before baseline-relative experimental comparison; no behavioural change is expected. See `docs/release_v4_32.md`.

## v4.31 AJ_24038155 Dialect v1.5 import directives

v4.31 advances the active language to **AJ_24038155 Dialect v1.5**. Exact source-authored `COMMENT import <module>`, `COMMENT import <module> AS <alias>`, `COMMENT from <module> import <name-list>`, and `COMMENT from <module> import *` forms are now executable import directives represented by a dedicated `ImportDirectiveNode`; all other `COMMENT` text remains non-executable. v1.5 also defines the exact adapter `string_method_punctuation -> string.punctuation`. This makes the frozen Algorithms 5 and 7 library dependency semantics explicit rather than compiler-inferred. Baseline processing remains fixed to **AJ_DIALECT_STRICT**. Scoring Rubric v1.1, Scoring Schema v1.4, and Common Tests v1.1 (50 suites / 113 tests) remain unchanged. See `docs/AJ_24038155_Dialect_v1_5.md`, `docs/AJ_24038155_dialect_v1.4_to_v1.5_update.md`, and `docs/release_v4_31.md`.

## v4.30 dependency-aware calibration currentness

v4.30 fixes resume/currentness for Common Tests that declare optional external modules. A calibration manifest now records the availability and installed distribution version of every module named in `requires_modules`. If that environment changes—for example, NumPy/Matplotlib are installed after a prior `MISSING_DEPENDENCY` result—the affected algorithm is no longer treated as `SKIPPED_CURRENT` and is automatically reprocessed. Algorithms whose declared dependency environment is unchanged remain resumable. Baseline processing remains fixed to **AJ_DIALECT_STRICT** and Common Tests v1.1 remain unchanged (50 suites / 113 tests). See `docs/release_v4_30.md`.

# NL Flow Diagram Encoder Pipeline v4.29

## v4.29 Algorithm 50 external-module correction

v4.29 adds deterministic lowering for the explicit NumPy/Matplotlib adapter calls used by the frozen Algorithm 50 Strict pseudocode. Baseline Benchmark Folder processing remains fixed to **AJ_DIALECT_STRICT** and Common Tests v1.1 remain unchanged (50 suites / 113 tests). See `docs/release_v4_29.md`.

# NL-FDEP

## v4.28 benchmark execution and Python representation correction

v4.28 keeps **AJ_24038155 Dialect v1.4**, **Scoring Rubric v1.1**, **Scoring Schema v1.4**, and **Common Test Design v1.1 (50 suites / 113 tests)** unchanged. Baseline Benchmark Folder processing remains fixed to **AJ_DIALECT_STRICT**.

The release adds conservative support for six historically truncated packaged `algorithm_title` values when creating a temporary executable view of frozen reference Python, lowers source-authored `RAISE SystemExit` as real Python termination, and publishes aliases for AJ protected method names that Python would otherwise privately name-mangle. Frozen benchmark files and Common Test executable arrays are not changed. See `docs/release_v4_28.md`.

## v4.27 behavioural oracle execution contract correction

v4.27 introduced the controlled non-mutating reference execution view, rejected accidental reference runtime faults as normal expected behaviour, lowered Strict AJ `LOWERCASE`/`UPPERCASE`/`CHARACTERS_OF` intrinsics, and made `QUIT`/`STOP` deterministic under isolated execution. See `docs/release_v4_27.md`.

## v4.26 strict benchmark standard restoration

v4.26 restores **AJ_DIALECT_STRICT** as the controlled profile for all Baseline Benchmark Folder processing. The baseline corpus is the AJ_24038155 Dialect v1.4 reference standard and is therefore not passed through Generic Compatibility recovery. Experimental inputs retain their independently selected profile. Packaged Common Tests v1.1 (50 suites / 113 tests), Rubric v1.1, Scoring Schema v1.4 and AJ Dialect v1.4 are unchanged.

Baseline profile provenance is now explicit: Strict-profile v4.26 calibrations are current; calibrations produced under Generic Compatibility or earlier pipeline versions are stale and must not be reused for baseline-relative comparison. The CLI baseline command also defaults to Strict. See `docs/release_v4_26.md`.

# NL Flow Diagram Encoder Pipeline

## v4.25 calibration-availability and partial-benchmark correction

v4.25 keeps **AJ_24038155 Dialect v1.4**, **Scoring Rubric v1.1**, **Scoring Schema v1.4**, **Common Test Design v1.1**, and test-spec schema **v1.2** unchanged.

The baseline study now separates **calibration availability** from **behavioural agreement**. If generated baseline Python reaches behavioural testing and an evaluated calibration percentage is produced, the algorithm is `CALIBRATED` even when the score is 0% and the pipeline's legacy overall status is `FAILURE` because one or more behavioural tests disagreed with the trusted reference. `PIPELINE_FAILURE` is reserved for algorithms that never produced an evaluated calibration.

A partially calibrated benchmark no longer blocks the whole experimental study. The runner records how many of the 50 algorithms have evaluated baseline calibrations, identifies unavailable structural/non-evaluable cases, and allows the user to continue after an explicit warning. Algorithms without an eligible calibration remain `NOT_EVALUABLE` for baseline-relative behavioural comparison; no score is invented. Current terminal partial calibrations are recognised so the dependency guard does not repeatedly offer the same recalibration on every experimental run.

The runtime-selected baseline still uses the controlled `GENERIC_COMPATIBILITY` profile and the packaged **50 Common Test v1.1 suites / 113 tests**. See `docs/release_v4_25.md`.

## v4.22 descriptive G2 behavioural evidence profiles

v4.22 keeps **AJ_24038155 Dialect v1.4** and the 16 scored C1-P4 criteria unchanged. The existing non-scored **G2 Behavioural Evidence Adequacy** gate is expanded from a one-word headline into a descriptive evidence profile with declared/evaluable/pass counts, six coverage dimensions, strengths, limitations, coverage basis and interpretation guidance. The short `ADEQUATE` / `PARTIAL` / `LIMITED` label remains only for sorting and aggregation.

The separately distributed common-test pack advances to **Test Design v1.1** / test-spec schema **1.2**. Its 113 tests are unchanged; each of the 50 suites now declares its own descriptive G2 evidence profile. Runtime scoring combines that declaration with what actually executed. Human review and analysis exports also preserve the full G2 description. See `docs/release_v4_22.md`.

## v4.20 calibrated baseline comparison design

v4.20 keeps **AJ_24038155 Dialect v1.4** and the v1.0 rubric criteria unchanged, while formalising the study comparison design. Frozen baseline pseudocode is processed through the same pipeline and compared behaviourally with the trusted baseline Python to produce a **Baseline Calibration Score**. Experimental pseudocode is processed through the same pipeline and compared against the same trusted baseline Python and baseline-owned `Algorithm n Tests.json` cases to produce an **Experimental Behavioural Score**. The pipeline reports both values side by side plus a descriptive percentage-point delta (`experimental - baseline`); this delta is not an adjusted accuracy score or causal correction.

Baseline Python with no independent expected outcomes is explicitly labelled `TRUSTED_REFERENCE`, not falsely `VALIDATED`. Experimental runs may use reference-derived expectations only after a current v4.20 baseline calibration exists. New artefacts include `baseline_calibration.json`, `baseline_relative_comparison.json`, and `study_analysis/baseline_comparison.csv`. See `docs/release_v4_20.md`.

## v4.19 frozen baseline Python reference discovery

v4.19 keeps **AJ_24038155 Dialect v1.4** and the v1.0 scoring criteria unchanged. Baseline reference discovery now accepts `Algorithm n Baseline Python code.py` and `Algorithm n Baseline Python code.txt` as authoritative Python sources, while preserving legacy `Algorithm n Python.py` and exactly-one-`.py` fallback support. A `.txt` baseline reference is executed as Python source without modifying the frozen file. Multiple explicitly recognised reference files are treated as ambiguous. Reference discovery remains separate from `Algorithm n Tests.json` discovery.

## v4.18 study-safety and artefact-integrity hardening

v4.18 keeps **AJ_24038155 Dialect v1.4** and the v1.0 scoring criteria unchanged. It hardens study execution around reruns, resume completeness, behavioural-oracle derivation and aggregate reporting. Previous per-algorithm artefacts are archived before reprocessing so stale generated Python/AST/scoring files cannot contaminate a new run; resume requires a fully finalised artefact set; unscored batch/preflight failures remain visible in analysis tables; and baseline console reporting now distinguishes pipeline execution status from baseline calibration status.

Behavioural expectations now fail closed: omitted output/return/error fields remain unchecked unless they are explicitly supplied or derived from an independently `VALIDATED` reference Python run. Reference timeouts and unvalidated/missing baseline validation therefore cannot manufacture default expectations or act as hidden oracles. See `docs/release_v4_18.md`.

## v4.17 analysis provenance and version-consistency fix

v4.17 introduced correct study-layer version provenance and immutable `study_analysis/run_history/<batch_run_id>/` snapshots while retaining latest-view analysis files. AJ Dialect v1.4 remained unchanged. See `docs/release_v4_17.md`.

## v4.16 source-neutral naming cleanup

v4.16 keeps **AJ_24038155 Dialect v1.4** and pipeline semantics unchanged. Historical AI-agent/vendor names have been removed from distributed filenames, tests, documentation, manifests, comments and internal identifiers. Corpus-derived regression cases now use anonymous `source_a` through `source_f` identifiers only where a stable fixture distinction is needed; reusable implementation helpers are named for the syntax/behaviour they handle rather than for a source. Corpus adapters are format-driven (`NumberedSectionAdapter`, `ExampleSectionAdapter`, `StructuredExportAdapter`, and `TextExportAdapter`). This is a naming and packaging neutrality change only; no normalisation rule is selected by a vendor/model identity.

Validation: 1,194 pytest tests passed, 3 skipped, 5 subtests; 344 unittest tests passed, 1 skipped. See `docs/release_v4_16.md`.

## v4.15 corpus-fixture cleanup

v4.15 keeps **AJ_24038155 Dialect v1.4** unchanged. The bundled `tests/corpora/` research-response fixtures and the regression tests that required those files have been removed from the distributable pipeline package. Research corpora remain external study inputs rather than implementation dependencies. The remaining regression suite continues to test parser, normalisation, AST, flow, compiler, study and scoring behaviour without bundled model-response datasets.

`pycharm_runner.py`, `README.md`, `requirements.txt`, `VERSION`, and `pytest.ini` remain visible at the project root. See `docs/release_v4_15.md`.

## v4.14 project structure cleanup

v4.14 keeps **AJ_24038155 Dialect v1.4** unchanged and reorganises the package for easier use in PyCharm and study maintenance. `pycharm_runner.py` remains visible at the project root; implementation files are grouped by responsibility. A root `requirements.txt` is included for environment setup. See `docs/release_v4_14.md`.

### Project layout

```text
NL_Flow_Diagram_Encoder_Pipeline_v4_27/
├── pycharm_runner.py
├── README.md
├── requirements.txt
├── VERSION
├── pytest.ini
├── manifests/
├── flow diagram components/
├── parser components/
├── compiler components/
├── pipeline components/
├── study components/
├── study data/
│   ├── common tests v1.1/
│   ├── common tests v1.3/
│   └── common tests v1.4.2/ (active RC10 corrected pack; v1.4 retained for provenance)
├── cli components/
├── examples/
├── docs/
└── tests/
```

### Setup

From the project root:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python -m unittest discover -s tests -t . -q
```

The pipeline itself uses Python standard-library modules. The interactive PyCharm runner uses `tkinter`; on platforms where Tk is not bundled with Python, install the platform's Python/Tk package.

## v4.13 AJ_24038155 Dialect v1.4 runtime type inspection

v4.13 advances the active dialect to AJ_24038155 v1.4. It adds canonical `CALL ISINSTANCE(value, type_reference)` runtime type inspection as a dedicated `IsInstanceNode`, including multi-type forms such as `CALL ISINSTANCE(value, (INTEGER, FLOAT))`, with deterministic Python `isinstance(...)` lowering. No implicit type tests or conversions are introduced. See `docs/AJ_24038155_Dialect_v1_4.md` and `docs/release_v4_13.md`.

## v4.12 indexed reserved-identifier normalisation fix (AJ_24038155 Dialect v1.3)

v4.12 keeps AJ_24038155 Dialect v1.3 unchanged. It fixes source-proven reserved identifiers such as `list`/`set` when subsequently used with indexing (`list[i]`), ensuring the established internal escape is propagated rather than misreading the occurrence as literal syntax. Baseline source names remain untouched. See `docs/release_v4_12.md`.

## v4.11 Source-identifier normalisation completion (AJ_24038155 Dialect v1.3)

v4.11 keeps AJ_24038155 Dialect v1.3 unchanged and completes the source-proven reserved-identifier normalisation used by study baselines. Baseline pseudocode may preserve Python/source identifiers exactly even when they collide case-insensitively with AJ keywords. The processor now propagates a proven escaped identifier into simple `STRING("{identifier}")` placeholders and treats a reserved spelling after `.` as an unambiguous member/property identifier, including source forms such as `os.path.join(...)` and `swarm.step(...)`. These are representation-only normalisations logged under the existing `RESERVED_IDENTIFIER_ESCAPE` rule family; baseline source files must not be pre-prefixed. See `docs/release_v4_11.md`.

## v4.10 AJ_24038155 Dialect v1.3 explicit casts and QUIT

v4.10 advances the active dialect to AJ_24038155 v1.3. It adds explicit runtime primitive casts `CALL INTEGER(expression)`, `CALL FLOAT(expression)`, and `CALL STRING(expression)` as first-class `CastNode` expressions with deterministic Python `int`/`float`/`str` lowering, while preserving the distinction from typed literal constructors. It also adds canonical `QUIT` as a dedicated top-level/block program-termination statement (`QuitNode`) lowering to Python `quit()` and remaining terminal through the flow graph. `QUIT` participates in the existing source-proven reserved-identifier escape convention when binding syntax proves that spelling denotes an identifier. Legacy `STOP` remains accepted for compatibility. No implicit casts, runtime type inspection, substring operation, Boolean/CHAR casts, callbacks, or first-class function values are added. See `docs/AJ_24038155_Dialect_v1_3.md` and `docs/release_v4_10.md`.

## v4.09 reserved-identifier evidence fix

v4.09 preserves the v4.08 experimental infrastructure and AJ_24038155 Dialect v1.2 semantics while extending the established `__reserved_keyword__` compatibility convention to strict AJ source when an AJ keyword is proven to be used as an identifier by an unambiguous binding position (for example `string <- ...` or `FOR EACH char IN ...`). The escape is source-proven, logged as semantic-preserving evidence, propagated to corresponding identifier uses, and does not rewrite constructors such as `STRING(...)`/`CHAR(...)` or quoted text. It does not repair unrelated source-semantic errors such as a top-level `RETURN`. See `docs/release_v4_09.md`.

## v4.08 experimental-infrastructure freeze

v4.08 adds automatic study pre-flight validation, immutable SHA-256/run provenance, resume and reviewed-output protection, independent baseline-reference validation, a paired direct-AST vs flow-mediated behavioural control, and an integrated human-review dashboard. It preserves the v4.07 AJ v1.2 language/compiler semantics. The legacy AST-vs-flow rubric difference remains descriptive only; `flow_mediation_delta` is the paired behavioural measure for the machine-readable intermediate representation. If a reference Python fails researcher-specified expected outcomes it is marked `REFERENCE_VALIDATION_FAILED` and is not used to derive omitted test expectations. Validation: 1,157 pytest passed, 3 skipped, 5 subtests passed; 344 unittest tests passed, 1 skipped. See `docs/release_v4_08.md` and `docs/study_folder_layout_v4_08.md`.

## v4.07 study batch, benchmark, scoring and human-review layer

v4.07 adds reproducible study-folder processing, baseline Python benchmarking, a versioned evidence-based scoring rubric (G1, C1-P4), portable human-review questionnaires, adjudication, and analysis-ready JSON/CSV outputs. Batch mode processes `Algorithm - n/Algorithm n Pseudocode.txt` independently and writes evidence back into each algorithm's `pipeline_artifacts/` folder. Baseline pseudocode is processed through the same pipeline and, where `Algorithm n Tests.json` exists, generated Python is behaviourally compared with supplied reference Python. Descriptive Python source/AST similarity is retained but is not treated as correctness. During scoring validation, a semantic flow-graph defect was found and corrected: BREAK/CONTINUE/RETURN/RAISE/STOP paths now preserve terminal/control-transfer behaviour in the visual flow graph, including nested-loop BREAK semantics. No AJ v1.2 language rule changes. Validation: 1,152 pytest passed, 3 skipped, 5 subtests passed; 339 unittest passed, 1 skipped. See `docs/release_v4_07.md`, `docs/study_folder_layout_v4_07.md`, and `docs/scoring_rubric_v1_0.json`.

## v4.06 dictionary GET missing-key semantics and JOIN compatibility

v4.06 makes AJ v1.2 one-argument dictionary `GET` preserve its specified missing-key runtime error by lowering to Python indexing, while two-argument `GET(key, default)` retains `.get(key, default)`. It also packages the validated post-v4.05 JOIN static-compatibility rule: no implicit element stringification is invented, known JOIN elements/separators must be text-compatible, and unknown types remain uninferred. Unknown receiver `.GET(...)` calls remain ordinary user-defined methods. No AJ dialect source document is changed. Full validation: 1141 pytest passed, 3 skipped, 5 subtests passed; 332 unittest passed, 1 skipped. See `docs/release_v4_06.md`.

## v4.05 safe AJ OUTPUT placeholders and static-semantic completion

v4.05 fixes AJ v1.2 OUTPUT placeholder handling so only exact `{identifier}` forms are substituted and scope-checked. Arbitrary brace content such as `{1+2}`, Python-style format specs/conversions, and doubled braces remain literal text rather than being handed to Python's f-string evaluator. The release also packages the validated post-v4.04 member-method arity checks and declared-type value-entry compatibility checks. Unknown receiver/value types remain uninferred. No AJ dialect source document is changed. Full validation: 1129 pytest passed, 3 skipped, 5 subtests passed; 332 unittest passed, 1 skipped. See `docs/release_v4_05.md`.

## v4.04 canonical RANDOM expression support

v4.04 adds first-class parser, flow-diagram, static-semantic, and Python-compiler support for frozen AJ v1.2 `RANDOM INT(minimum, maximum)`, `RANDOM FLOAT(minimum, maximum)`, and `RANDOM BOOLEAN()` expressions. `RANDOM INT` uses Python `randint` to preserve AJ's explicitly inclusive endpoints. Because AJ v1.2 does not define distributions for FLOAT or BOOLEAN, v4.04 documents compiler backing conventions of Python `uniform(a, b)` and unbiased `bool(getrandbits(1))` respectively; these are implementation conventions rather than new dialect guarantees. The compiler uses a fresh module alias so source identifiers cannot shadow the random backing. Known invalid bound types are rejected conservatively while unknown parameter types remain uninferred. No AJ dialect source document is changed. Full validation: 1103 pytest passed, 3 skipped, 5 subtests passed; 332 unittest passed, 1 skipped. See `docs/release_v4_04.md`.

## v4.03 frozen collection-grammar completion

v4.03 adds first-class parser, flow-diagram, static-semantic, and Python-compiler support for frozen AJ v1.2 collection forms that were previously absent from the executable pipeline: `INSERT value INTO collection AT index`, `REMOVE value FROM collection`, `SET [values]`, `UNION(set1, set2)`, `INTERSECTION(set1, set2)`, and `DIFFERENCE(set1, set2)`. INSERT lowers to Python list `.insert(index, value)`; specific-value removal lowers to `.remove(value)` for LIST/SET-backed collections without inventing missing-value guards; set literals and operations lower to native Python set representations/operators and establish SET backing for later APPEND lowering. New operation words are contextual where needed, preserving existing identifiers and methods such as `METHOD Remove` and `FUNCTION Union`. This compiler release also packages the validated post-v4.02 static-semantic refinements: exact arity for lexically resolved AJ functions, narrow explicit-known-type compatibility checks, and rejection of valued returns from constructors while permitting value-less early returns. No AJ dialect source document is changed. Full validation: 1095 pytest passed, 3 skipped, 5 subtests passed; 332 unittest passed, 1 skipped. See `docs/release_v4_03.md`.

## v4.02 termination-aware collection flow and packaged semantic-validator refinements

v4.02 makes compiler collection-representation merging aware of non-fallthrough control-flow paths: branches that `RETURN` or `RAISE` no longer pollute the representation state seen by following code, `TRY/CATCH` merges only reachable post-try paths rather than adding the pre-try state as a fictitious third outcome, and zero-iteration loop paths are preserved without allowing always-terminating loop bodies to erase valid incoming collection evidence, and BREAK/CONTINUE paths are tracked explicitly so abrupt loop control does not pollute later statements while still contributing conservatively to post-loop state. This compiler release also packages the validated post-v4.01 static-semantic refinements: conservative bare-identifier definite assignment across IF/ELSE, loops and TRY/CATCH, plus flow-sensitive lexical dictionary `GET` intrinsic resolution; BREAK/CONTINUE non-fallthrough is aligned across these semantic analyses, and named catch binders remain catch-local even when the catch path is the only path reaching ENDTRY. No AJ dialect change is introduced. Full validation: 1052 pytest passed, 3 skipped, 5 subtests passed; 332 unittest passed, 1 skipped. See `docs/release_v4_02.md`.

## v4.01 flow-sensitive collection representation tracking

v4.01 makes compiler collection representation evidence follow source order within each lexical scope. Explicit SET assignments/conversions establish `.add()` backing, LIST assignments/conversions clear it, later assignments no longer retroactively affect earlier APPEND operations, and control-flow merges retain SET evidence only when every possible path agrees. No AJ dialect change is introduced. Full validation: 1015 pytest passed, 3 skipped, 5 subtests passed; 332 unittest passed, 1 skipped. See `docs/release_v4_01.md`.

## v4.00 lexical binding isolation for loop and catch variables

v4.00 extends compiler lexical-name isolation to every active canonical AJ binding site: `FOR EACH` variables, `FOR ... IN RANGE` variables, named `CATCH` variables, and nested function declaration names now remain local even when a class property or enclosing collection hint has the same spelling. Assignment targets and parameters retain the v3.99 behaviour, explicit `THIS.name` remains instance state, and legacy no-`PROPERTY` inferred-state compatibility is unchanged. No AJ dialect change is introduced. Guarded unresolved-abstraction lookup is also lexical, so nested helper definitions no longer leak into sibling scopes. Full validation: 1009 pytest passed, 3 skipped, 5 subtests passed; 332 unittest passed, 1 skipped. See `docs/release_v4_00.md`.

## v3.99 explicit class-state and local-name scope isolation

v3.99 fixes compiler name resolution inside canonical AJ classes: explicit `THIS.name` remains instance state, while same-spelled unqualified assignments in methods/constructors remain local bindings; nested helpers preserve lexical shadowing as well. The older no-`PROPERTY` generic-compatibility path for inferred object state remains intact. No AJ dialect change is introduced. Full validation: 1001 pytest passed, 3 skipped, 5 subtests passed; 332 unittest passed, 1 skipped. See `docs/release_v3_99.md`.

## v3.98 lexical collection-type scope isolation

v3.98 makes compiler collection representation evidence lexical rather than program-wide: same-spelled locals in sibling functions/methods no longer leak SET backing into one another, parameters/local assignments shadow enclosing evidence, and unshadowed enclosing SET evidence remains available to nested functions. This release also packages the previously validated single-file `1. <title>` metadata handling and the INTEGER DIVISION negative-semantics audit note. No AJ dialect change is introduced. Full validation: 997 pytest passed, 3 skipped, 5 subtests passed; 332 unittest passed, 1 skipped. See `docs/release_v3_98.md`.

## v3.97 unresolved N-Queens core abstraction guard

v3.97 prevents undefined `isSafe(...)` and `emptyBoard(...)` calls from being treated as executable external dependencies. These helpers carry core N-Queens algorithm and board-representation semantics, so they now produce an expected failure before Python generation unless explicitly defined in the supplied AJ source. Unrelated external calls remain permitted. No AJ dialect change is introduced. Full validation: 989 pytest passed, 3 skipped, 5 subtests passed; 329 unittest passed, 1 skipped. See `docs/release_v3_97.md`.

## v3.96 FOR EACH rebinding semantics and explicit REVERSE mutation

v3.96 removes compiler-invented write-back from `FOR EACH` loop-variable assignments: rebinding the current item now remains local to the loop variable instead of silently generating `collection[index] = item`. Standalone source `REVERSE target` is correspondingly preserved as explicit in-place mutation via `CALL reverse_list(target)` / Python `.reverse()`, so matrix-row reversal continues to mutate the row object without relying on artificial loop write-back. No AJ dialect change is introduced. Full validation: 985 pytest passed, 3 skipped, 5 subtests passed; 329 unittest passed, 1 skipped. See `docs/release_v3_96.md`.

## v3.95 unresolved punctuation dependency enforcement

v3.95 completes the v3.94 punctuation boundary by rejecting undefined `CALL is_punctuation(value)` before Python generation. The compiler now returns an expected-failure result unless the supplied AJ program explicitly defines the exact `is_punctuation` helper; a supplied definition remains authoritative. Accepted singular character predicates (`is_number`, `is_digit`, `is_uppercase`) are unchanged. No AJ dialect change is introduced. Full validation: 983 pytest passed, 3 skipped, 5 subtests passed; 327 unittest passed, 1 skipped. See `docs/release_v3_95.md`.

## v3.94 punctuation predicate compiler boundary

v3.94 removes the compiler-owned `is_punctuation(value)` interpretation. Canonical `CALL is_punctuation(value)` is now preserved as an ordinary helper/dependency call instead of being silently lowered to a compiler-selected `not str(value).isalnum() and not str(value).isspace()` predicate. This keeps explicitly supplied/imported punctuation semantics authoritative and leaves undefined punctuation abstractions unresolved, while retaining the accepted singular character intrinsics `is_digit(value) -> value.isdigit()` and `is_uppercase(value) -> value.isupper()`. No AJ dialect change is introduced. Full validation: 983 pytest passed, 3 skipped, 5 subtests passed; 327 unittest passed, 1 skipped. See `docs/release_v3_94.md`.

## v3.93 Python compiler generated-temporary hygiene

v3.93 extends the v3.92 fresh-name invariant to compiler-only Python temporaries used for nested PUSH/POP transfers, nested ENQUEUE/DEQUEUE transfers, and indexed SWAP lowering. The compiler retains `temp` when free, but deterministically selects `temp_1`, `temp_2`, and so on when source identifiers already occupy those names. This prevents generated implementation state from capturing or overwriting user variables while preserving the source abstractions exactly. No AJ dialect grammar or primitive semantics change is introduced. Full validation: 980 pytest passed, 3 skipped, 5 subtests passed; 327 unittest passed, 1 skipped. AJ v1.1 and v1.2 hashes are unchanged. See `docs/release_v3_93.md`.

## v3.92 SWAP generated-temporary hygiene

v3.92 keeps the existing semantics-preserving `SWAP` lowering but makes its implementation temporary hygienic. `temp_var` is now treated as a preferred metavariable spelling rather than a mandatory source-visible identifier: if that name already occurs anywhere in the input algorithm, the compatibility layer deterministically selects `temp_var_1`, `temp_var_2`, and so on until it finds an unused, non-keyword identifier. This prevents a generated swap temporary from capturing or overwriting user state while preserving existing output when `temp_var` is free. No AJ dialect grammar or `SWAP` semantics change is introduced. Full validation: 976 pytest passed, 3 skipped, 5 subtests passed; 323 unittest passed, 1 skipped. AJ v1.1 and v1.2 hashes are unchanged. See `docs/release_v3_92.md`.

## v3.91 accumulated semantic-integrity corrections and character-predicate compiler tightening

v3.91 packages the unreleased semantic/audit corrections accumulated after v3.90 and is numbered because this batch now includes a compiler change. GC230 plus the duplicate GC158 numeric-to-string repair are retired, so omitted string conversions remain expected source failures; unknown-representation `PUSH item TO receiver` now preserves `CALL PUSH(...)` rather than asserting LIST/APPEND semantics; the GC245 source_d N-Queens `set + {item}` interpretation is retained with a detailed evidence/refusal-boundary audit; and compiler lowering for `is_digit(value)` / `is_uppercase(value)` now uses direct `value.isdigit()` / `value.isupper()` without an invented `str(...)` conversion. source_d Algorithm 24 remains valid because its `char` values are independently evidenced by iteration over `password`. Full validation: 972 pytest passed, 3 skipped, 5 subtests passed; 323 unittest passed, 1 skipped. AJ v1.1 and v1.2 hashes are unchanged. See `docs/release_v3_91.md`.

## v3.90 source_f Algorithm 27 source-arithmetic expected-failure audit

v3.90 is an audit-only release: production normalisation/compiler behaviour is unchanged. source_f Algorithm 27 continues to preserve source-authored `N / 2` as ordinary division, so generated Python retains `len(matrix) / 2` and is intentionally classified as an expected executable-correctness failure when `range(...)` receives the float bound. The audit now explicitly records that the surrounding matrix-rotation algorithm is otherwise viable: an audit-only counterfactual replacing only `/` with integer division correctly rotates representative 2x2, 3x3, and 4x4 matrices. The counterfactual is diagnostic evidence only and is not applied by the pipeline. See `docs/source_f_algorithm27_source_division_expected_failure_audit_v3_90.md`.

## v3.89 retire GC214; preserve `unique(...)` SET return semantics

v3.89 applies the user-confirmed rule that exact one-argument `unique(collection)` denotes SET conversion. GC214 is retired from the active compatibility sequence because removing `unique(result)` changes the return type from SET to LIST even when guarded appends already prove the values are duplicate-free. GC222 now consistently preserves every eligible exact `unique(name)` as `CALL to_set(name)`, compiling to Python `set(name)`. The source_f unsorted-list intersection therefore returns a set rather than silently losing its explicit `unique(...)` type semantics. Full validation: 963 pytest passed, 3 skipped, 5 subtests passed; 323 unittest passed, 1 skipped. Historical AJ v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`; active AJ v1.2 SHA-256 remains `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.

See `docs/release_v3_89.md` and `tests/test_gc214_retirement_unique_set_semantics_v3_89.py`.

## v3.88 GC215 class recovery with unresolved ordering abstractions

v3.88 keeps GC215's source-evidenced class/state recovery for the source_f ordered-cache shape but removes the invented LRU implementation. `moveToFront`, `removeBack`, and `addToFront` remain explicit opaque CALLs after `THIS.cache` qualification; if they are not explicitly defined, the Python compiler now returns an expected unresolved-abstraction failure with no source code emitted. The capacity-like state remains a constructor argument and cache remains internally initialised key/value dictionary state. Explicit zero-argument `orderedDict()` also now uses ordinary Python `{}` backing rather than `collections.OrderedDict()`; ordering semantics must come from source-authored operations. Full validation: 961 pytest passed, 3 skipped, 5 subtests passed; 323 unittest passed, 1 skipped. Historical AJ v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`; active AJ v1.2 SHA-256 remains `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.

See `docs/release_v3_88.md`, `tests/test_source_f_algorithm35_evidenced_ordered_cache_adt_v3_15.py`, and `tests/test_unresolved_ordered_cache_abstractions_v3_88.py`.

## v3.87 explicit orderedDict compiler lowering

v3.87 keeps an explicitly authored zero-argument `orderedDict()` constructor source-faithful as `CALL orderedDict()` in canonical AJ, but now lowers that compatibility call to Python `__import__('collections').OrderedDict()` instead of emitting an undefined `orderedDict()` call. The generic source phrase `ordered dictionary` remains `CALL create_ordered_dictionary()` with normal insertion-ordered Python `dict` backing, and plain dictionary/hash-map forms remain unchanged. No LRU policy or missing algorithmic operation is invented. Full validation: 958 pytest passed, 3 skipped, 5 subtests passed; 323 unittest passed, 1 skipped. Historical AJ v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`; active AJ v1.2 SHA-256 remains `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.

See `docs/release_v3_87.md` and `tests/test_explicit_ordereddict_compiler_lowering_v3_87.py`.

## v3.86 source-abstraction constructor preservation

v3.86 completes the current generic constructor/conversion abstraction audit. GC209 now preserves explicit `array(value)` as `CALL to_array(value)` instead of exposing a LIST conversion; Python still lowers the array to mutable `list(value)` storage as a compiler implementation detail. GC030 now preserves explicit `ordered dictionary` as `CALL create_ordered_dictionary()` instead of weakening it to `EMPTY DICTIONARY`; Python uses insertion-ordered `dict` storage underneath. The audit confirmed that list/set/plain-dictionary and the previously repaired STACK/QUEUE/DEQUE paths are already source-faithful and require no additional change. Full validation: 954 pytest passed, 3 skipped, 5 subtests passed; 323 unittest passed, 1 skipped. Historical AJ v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`; active AJ v1.2 SHA-256 remains `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.

See `docs/release_v3_86.md` and `tests/test_array_constructor_abstraction_preservation_v3_86.py`.

## v3.85 explicit empty-array abstraction preservation

v3.85 stops explicitly authored `empty array` / `EMPTY ARRAY` from canonicalising as `EMPTY LIST`. Assignment-style declarations now use `CALL create_array(0, NONE)`, and command-style `CREATE empty array name` uses the same array abstraction; explicit empty lists remain `EMPTY LIST`. Python may lower the zero-length array to `[None] * 0`, but later indexed writes are preserved as indexed writes and still fail when no capacity was supplied—no APPEND/growth behaviour or hidden capacity is invented. Full validation: 948 pytest passed, 3 skipped, 5 subtests passed; 323 unittest passed, 1 skipped. Historical AJ v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`; active AJ v1.2 SHA-256 remains `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.

See `docs/release_v3_85.md` and `tests/test_empty_array_abstraction_preservation_v3_85.py`.

## v3.84 explicit NULL source-preservation

v3.84 stops generic compatibility normalisation from rewriting an explicitly authored `NULL` token as the legacy `CALL NULL()` form. Source `NULL` now remains textually `NULL` in processed AJ; `IS NULL` / `IS NOT NULL` normalise only to `== NULL` / `!= NULL`. Native `None`, `none`, and `NONE` still canonicalise to AJ v1.2 `NONE`, while an explicitly authored legacy `CALL NULL()` remains accepted. Python lowering maps both preserved `NULL` and native `NONE` to `None`, and null comparisons use `is None` / `is not None`. Quoted `"NULL"` text is unchanged. Full validation: 944 pytest passed, 3 skipped, 5 subtests passed; 323 unittest passed, 1 skipped. Historical AJ v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`; active AJ v1.2 SHA-256 remains `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.

See `docs/release_v3_84.md` and `tests/test_explicit_null_preservation_v3_84.py`.

## v3.83 explicit deque abstraction preservation

v3.83 stops explicitly declared deques from canonicalising as `EMPTY LIST`. Source-evidenced `empty deque` / `EMPTY DEQUE`, `empty DoubleEndedQueue`, and zero-argument `Deque()` / `DoubleEndedQueue()` construction now use `CALL create_deque()` in canonical AJ. Front/back behaviour remains explicit through `CALL deque_is_empty(...)`, `CALL deque_size(...)`, `CALL deque_front(...)`, `CALL deque_back(...)`, `CALL deque_pop_front(...)`, `CALL deque_pop_back(...)`, and `CALL deque_push_back(...)`; Python may still lower those operations to list-backed `[]`, indexing, `.append(...)`, `.pop(0)`, `.pop(-1)`, and `len(...)` as implementation details. GC237 now preserves its source-evidenced `REMOVE FRONT`, `REMOVE BACK`, and `ADD BACK` surfaces as deque intrinsics rather than AJ list primitives. GC136 remains deliberately unchanged for sources that explicitly declare a LIST and merely use deque-like operations: those stay list-backed. Full validation: 940 pytest passed, 3 skipped, 5 subtests passed; 323 unittest passed, 1 skipped. Historical AJ v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`; active AJ v1.2 SHA-256 remains `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.

See `docs/release_v3_83.md` and `tests/test_abstract_deque_preservation_v3_83.py`.

## v3.82 explicit queue abstraction preservation

v3.82 stops explicitly declared queues from canonicalising as `EMPTY LIST`. `empty queue` / `EMPTY QUEUE` and the older `CREATE Empty Queue` recovery now use `CALL create_queue()`, `CALL ENQUEUE(queue, value)`, `CALL DEQUEUE(queue)`, `CALL queue_is_empty(queue)`, and `CALL queue_size(queue)` in canonical AJ; Python may still lower those operations to list-backed FIFO behaviour as an implementation detail. GC235 now preserves the same queue intrinsics when one-line structural expansion exposes late queue operations, while explicitly list-backed FIFO sources (`EMPTY LIST` / seeded list values) retain the historical `APPEND` / `REMOVE FIRST ITEM FROM` path. No queue type is inferred from operation names alone. Full validation: 936 pytest passed, 3 skipped, 5 subtests passed; 323 unittest passed, 1 skipped. Historical AJ v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`; active AJ v1.2 SHA-256 remains `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.

See `docs/release_v3_82.md` and `tests/test_abstract_queue_preservation_v3_82.py`.

## v3.81 GC244 explicit Stack() abstraction preservation

v3.81 changes GC244 so an evidenced zero-argument `Stack()` constructor used as class state no longer canonicalises to `EMPTY LIST`. Canonical AJ now preserves that state through `CALL create_stack()`, `CALL PUSH(...)`, `CALL POP(...)`, and `CALL stack_is_empty(...)`; Python may still use a list as the stack backing implementation. GC244 remains contextual and still refuses local `Stack()` calls, non-zero-argument constructors, later member rebinds, and unrelated explicit-list state. This aligns explicit `Stack()` with the abstract stack semantics already used for GC124 `CREATE Stack` and GC160 `empty stack`, while GC121's capacity-less array stack remains an expected failure. Full validation: 932 pytest passed, 3 skipped, 5 subtests passed; 319 unittest passed, 1 skipped. Historical AJ v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`; active AJ v1.2 SHA-256 remains `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.

## v3.80 generic explicit-stack abstraction preservation

v3.80 changes GC160 so an explicitly declared `empty stack` / `EMPTY STACK` no longer canonicalises to `EMPTY LIST`. The declaration now becomes `CALL create_stack()`, while source-evidenced stack operations remain `CALL PUSH(...)`, `CALL POP(...)`, and `CALL stack_is_empty(...)` in canonical AJ. Explicit stateful-class recovery preserves such fields as untyped stack properties rather than declaring them `AS LIST`; Python may still lower the explicit stack abstraction to `[]`, `.append(...)`, `.pop(-1)`, and `len(...) == 0` as implementation details. Explicit `EMPTY LIST` sources remain list-backed, and GC121's missing-capacity array stack remains an expected failure. Full validation: 929 pytest passed, 3 skipped, 5 subtests passed; 319 unittest passed, 1 skipped. Historical AJ v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`; active AJ v1.2 SHA-256 remains `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.

See `docs/release_v3_80.md` and `tests/test_gc160_abstract_stack_preservation_v3_80.py`.

## v3.79 implicit allocation zero-fill consistency

v3.79 changes GC223 so source_f's same-dimensions matrix-addition declaration `INIT result as R x C matrix` no longer invents zero-valued cells. The source-evidenced dimensions remain `LENGTH OF A` by `LENGTH OF A[0]`, while an unspecified initial cell value now canonicalises to `CALL create_matrix(..., NONE)` and compiles to a `None`-filled Python matrix until the source-supplied loop overwrites each cell. A consistency audit of all matrix/fixed-array allocation normalisers found no other unsupported zero fills: GC160, GC223 and GC224 use `NONE` for missing fills, while GC246, GC249 and generic zero-allocation surfaces retain `0` only when the source explicitly says `0`, `0s`, `filled with 0`, or `initialized with/to 0`. Full validation: 925 pytest passed, 3 skipped, 5 subtests passed; 315 unittest passed, 1 skipped. Historical AJ v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`; active AJ v1.2 SHA-256 remains `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.

See `docs/release_v3_79.md` and `tests/test_zero_fill_consistency_v3_79.py`.

## v3.78 GC224 preserves unspecified matrix cells with NONE

v3.78 removes GC224's silent zero-fill choice for source_f's linked matrix-multiplication declaration `INIT C as M x P matrix`. The source-proven dimensions remain `LENGTH OF A` by `LENGTH OF B[0]`, but an unspecified cell value now canonicalises to `CALL create_matrix(..., NONE)` and compiles to a `None`-filled Python matrix until the source-supplied multiplication loops overwrite each cell. An explicit `initialized with 0` / `initialised with 0` declaration remains zero-filled. The explicit accumulator `sum = 0` is unchanged. Full validation: 921 pytest passed, 3 skipped, 5 subtests passed; 315 unittest passed, 1 skipped. Historical AJ v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`; active AJ v1.2 SHA-256 remains `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.

See `docs/release_v3_78.md` and `tests/test_source_f_algorithm46_linked_matrix_multiplication_v3_22.py`.

## v3.77 GC196 class recovery requires stronger stateful-ADT evidence

v3.77 keeps GC196 for source_b Algorithm 37 but tightens its evidence gate now that AJ v1.2 can preserve genuine nested functions directly. In addition to the existing requirements (one top-level zero-argument container, explicit shared state, at least two nested operations, every nested operation referencing that state, and no outer call/return/output/control flow), GC196 now requires a type-like capitalised outer name and at least one nested operation that explicitly mutates declared shared state. Read-only helper groups and lower-case ordinary function containers therefore remain nested functions instead of being reclassified as classes. source_b `Stack` and the general `Bag` positive case still recover as classes because their nested operations visibly mutate shared collection state and the outer function neither calls nor returns those operations. Full validation: 919 pytest passed, 3 skipped, 5 subtests passed; 315 unittest passed, 1 skipped. Historical AJ v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`; active AJ v1.2 SHA-256 remains `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.

See `docs/release_v3_77.md` and `tests/test_source_b_algorithm37_stateful_adt_v2_82.py`.

## v3.76 GC124 preserves the abstract two-stack queue representation

v3.76 changes GC124 so source_a Algorithm 40 no longer canonicalises `CREATE Stack1` / `CREATE Stack2` as `EMPTY LIST` or represents stack emptiness with list-shaped `LENGTH OF` predicates. The canonical compatibility source now uses `CALL create_stack()` and `CALL stack_is_empty(...)`, while retaining the source-provided `PUSH`/`POP` operations. The Python compiler may lower these explicit stack abstractions to list-backed `[]`, `.append(...)`, `.pop(...)`, and length checks as implementation details. GC121 remains unchanged: the separate array-backed Algorithm 37 still fails when its capacity is absent. Full validation: 917 pytest passed, 3 skipped, 5 subtests passed; 313 unittest passed, 1 skipped. Historical AJ v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`; active AJ v1.2 SHA-256 remains `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.

See `docs/release_v3_76.md` and `tests/test_gc124_abstract_stack_preservation_v3_76.py`.

## v3.75 GC121 array-stack backing inference retired

v3.75 retires GC121's conversion of abstract `CREATE Stack` into `Stack <- EMPTY LIST` for source_a Algorithm 37. The source says the stack is array-backed and later performs indexed writes, but supplies no capacity or dimensions; choosing a dynamic empty list therefore invents a representation and is not semantically equivalent to the supplied indexed-write algorithm. GC121 still recovers the explicit PUSH/POP/PEEK operation boundaries, while `CREATE Stack` remains visibly unresolved so strict AJ v1.2 parsing stops before Python generation. No APPEND/POP/LENGTH replacement, class wrapper, or scope declaration is invented. source_a Algorithm 37 is now an intentional expected failure alongside Algorithm 38, and the corpus gate names both failures explicitly; the aggregate source_a parse floor changes from 37 to 36. Full validation: 913 pytest passed, 3 skipped, 5 subtests passed; 309 unittest passed, 1 skipped. Historical AJ v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`; active AJ v1.2 SHA-256 remains `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.

See `docs/release_v3_75.md` and `tests/test_gc121_array_stack_creation_retirement_v3_75.py`.

## v3.74 AJ_24038155 Dialect v1.2 nested functions

v3.74 advances the active dialect to AJ_24038155 v1.2. v1.2 formally permits lexical nested/local `FUNCTION ... ENDFUNCTION` declarations and requires Python generation to preserve that nesting rather than hoist local helpers. Callback and first-class function-value semantics remain explicitly out of scope for a later dialect revision. GC170 now uses this feature for source_a Algorithm 43: `INPUT N` becomes the external parameter of `FUNCTION unnamed_function ACCEPTS(N)`, the supplied `Hanoi` routine remains nested inside it, and the final Hanoi call stays inside the same outer computation. The former invented `input("Enter N")` / `integer_value(...)` path is removed. Full validation: 910 pytest passed, 3 skipped, 5 subtests passed; 306 unittest passed, 1 skipped. Historical AJ v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`; active AJ v1.2 SHA-256 is `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`.

See `docs/AJ_24038155_Dialect_v1_2.md`, `docs/release_v3_74.md`, and `tests/test_aj_v12_nested_functions_v3_74.py`.

## v3.73 GC160 parent-matrix dimension inference retired

v3.73 retires GC160's special-case expansion of `parent <- 2D array to store previous cell for reconstruction` into `CALL create_matrix(LENGTH OF maze, LENGTH OF maze[0], CALL NULL())`. The source does not state that `parent` has the same dimensions as `maze`, so the declaration now remains visibly unresolved and strict AJ parsing stops before Python generation rather than inventing dimensions. The separately evidenced declaration `visited <- 2D boolean array same size as maze initialized to BOOLEAN(False)` remains supported and still lowers to a maze-sized boolean matrix. source_c Algorithm 49 was already expected-fail because its maze-navigation semantics remain abstract, so no corpus parse floor changes. Full validation: 906 pytest passed, 3 skipped, 5 subtests passed; 306 unittest passed, 1 skipped. Frozen AJ_24038155 Dialect v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

See `docs/release_v3_73.md` and `tests/test_gc160_parent_matrix_dimension_retirement_v3_73.py`.

## v3.72 multi-value OUTPUT preserves argument semantics

v3.72 separates bare comma-separated output arguments from tuple data. Source `OUTPUT a, b` now canonicalises to the output-only compatibility form `OUTPUT CALL output_values(a, b)`, which compiles deterministically to Python `print(a, b)`. Explicit tuple data remains tuple data: both `OUTPUT (a, b)` and `OUTPUT TUPLE(a, b)` canonicalise/retain `OUTPUT TUPLE(a, b)` and compile to `print((a, b))`. source_a Algorithm 42 now follows the same generic output boundary rather than hard-coding a tuple. GC175's message-specific `OUTPUT STRING("Found at position {i}")` f-string recovery remains unchanged. Full validation: 903 pytest passed, 3 skipped, 5 subtests passed; 303 unittest passed, 1 skipped. Frozen AJ_24038155 Dialect v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

## v3.71 GC175 multi-part linear-search output preserves message semantics

v3.71 narrows GC175's handling of the explicit source_a Algorithm 9 output `OUTPUT "Found at position", i`. Instead of converting the two output components into tuple data, the canonical source now uses the existing AJ v1.1 placeholder form `OUTPUT STRING("Found at position {i}")`, which compiles deterministically to a Python f-string such as `print(f"Found at position {i}")`. Genuine source `TUPLE(...)` output remains tuple output. Full validation: 899 pytest passed, 3 skipped, 5 subtests passed; 303 unittest passed, 1 skipped. Frozen AJ_24038155 Dialect v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

## v3.70 GC160 uninitialised matrix storage uses NONE fill

v3.70 changes only the exact missing-fill declaration `target <- matrix of size rows x cols`: the source-supplied dimensions are preserved while the absent cell value is represented as `NONE`, yielding `CALL create_matrix(rows, cols, NONE)` and deterministic Python `[[None for _ in range(cols)] for _ in range(rows)]`. This avoids silently inventing numeric zero while still materialising the requested writable matrix storage. Explicit zero-filled forms such as `matrix of size rows x cols initialized with 0` and `rows * cols matrix of 0s` remain zero-filled. Full validation: 899 pytest passed, 3 skipped, 5 subtests passed; 303 unittest passed, 1 skipped. Frozen AJ_24038155 Dialect v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

See `docs/release_v3_70.md` and `tests/test_gc160_uninitialised_matrix_none_fill_v3_70.py`.

## v3.69 GC122 abstract character-frequency rescue retired

v3.69 retires the early GC122 rule that expanded `COUNT frequency of each character` into a complete dictionary-counting algorithm. The abstract operation is now preserved as unresolved source and source_a corpus Algorithm 38 is explicitly expected-fail; strict AJ parsing stops before Python generation rather than inventing missing counting logic. Full validation: 897 pytest passed, 3 skipped, 5 subtests passed; 301 unittest passed, 1 skipped. Frozen AJ_24038155 Dialect v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

See `docs/release_v3_69.md`, `tests/test_source_a_algorithm38_semantic_integrity.py`, and `tests/test_source_a_source_e_corpus_regression_v3_53.py`.

## v3.68 GC161 explicit `given_capacity` state

v3.68 closes the remaining GC161 visibility mismatch between canonical pseudocode and generated Python. Source `capacity <- GIVEN CAPACITY` is recovered as the explicit class state `given_capacity <- capacity`; the Python compiler therefore emits exactly one `self.given_capacity = capacity` rather than silently introducing `self.capacity = capacity`. Once that recovered state exists, executable references to the class-state name `capacity` inside the preserved LRU methods canonicalise to `given_capacity`, so pseudocode and Python use the same stored field. The constructor parameter remains `capacity`; quoted text/comments are not state references. GC161 continues to preserve source-written method bodies and does not add missing LRU steps. Full validation: 897 pytest passed, 3 skipped, 5 subtests passed; 301 unittest passed, 1 skipped. Frozen AJ_24038155 Dialect v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

See `docs/release_v3_68.md` and `tests/test_gc161_visible_capacity_state_v3_68.py`.

## v3.67 GC161 preserves source-written LRU method bodies

v3.67 narrows GC161 so the source_c `LRUCache` recogniser may recover the explicit class/constructor surface without replacing the source-written `get` and `put` algorithms. Method bodies are retained in source order. Explicit list/dictionary operations already present in those bodies may still be mapped to existing AJ compatibility intrinsics, but missing-key branches, recency operations, eviction logic, cache writes, or any other LRU steps are no longer manufactured. The exact source_c Algorithm 35 source remains executable because those LRU operations are explicitly supplied there.

See `docs/release_v3_67.md` and `tests/test_gc161_lru_body_preservation_v3_67.py`.

## v3.66 retire GC160 inferred string-to-character-list input conversion

v3.66 removes GC160's inference that a text-like `INPUT(...)` must become `CALL list_from_string(INPUT(...))` merely because the value is indexed and used with `LENGTH OF`. Both operations are valid on strings, so that evidence does not justify changing the input representation or return type. The input-resolution audit metadata is aligned with the same rule: no `STRING_TO_LIST_OF_CHARACTER` deterministic conversion is reported for this case.

Explicit `CALL list_from_string(...)` source remains supported, and the separate neutral unnamed-wrapper policy is unchanged. Full validation: 888 pytest passed, 3 skipped, 5 subtests passed; 301 unittest passed, 1 skipped. Frozen AJ_24038155 Dialect v1.1 SHA-256 remains `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`.

## v3.65 retire GC159 specialised level-order flattened-property inference

v3.65 removes GC159's remaining conversion of valid AJ identifiers `node_value`, `node_left`, and `node_right` into `node.value`, `node.left`, and `node.right` inside `FUNCTION LEVEL_ORDER_TRAVERSAL ACCEPTS(root)`, even when `node` is explicitly obtained from the traversal queue. The traversal context establishes the role of `node`, but it does not establish that a distinct underscored identifier denotes one of its properties. AJ_24038155 Dialect v1.1 permits underscores in identifiers and requires explicit `.` syntax for member access.

Explicit source member access such as `node.value`, `node.left`, and `node.right` remains unchanged. Historical flattened level-order fixtures now preserve their source identifiers rather than silently changing the represented algorithm. Where those identifiers appear in the validator's direct bare-read subset, ordinary declaration-before-use semantics apply; uses outside that deliberately conservative subset remain unresolved identifiers in generated code rather than being invented as members. No parser, compiler, intrinsic, or frozen AJ_24038155 Dialect v1.1 semantics change in v3.65.

## v3.64 retire GC159 Floyd flattened-property inference

v3.64 removes GC159's Floyd-specific conversion of valid AJ identifiers such as `slow_next`, `fast_next`, `tortoise_next`, and `hare_next` into `.next` member access merely because `slow`/`fast` or `tortoise`/`hare` are initialised from `head`. AJ_24038155 Dialect v1.1 permits underscores in identifiers and requires explicit `.` syntax for member access. Mixed forms such as `fast_next.next` are also preserved as written rather than being changed to `fast.next.next`.

Explicit source member access such as `slow.next` and `fast.next.next` remains unchanged. Historical flattened Floyd sources with undeclared `*_next` identifiers now reach the existing declaration-before-use semantic boundary instead of being silently repaired into a linked-list algorithm. No parser, compiler, intrinsic, or frozen AJ_24038155 Dialect v1.1 semantics change in v3.64.

## v3.63 retire GC146 updateInventory flattened transaction-property inference

v3.63 removes GC146's conversion of valid AJ identifiers `transaction_item`, `transaction_type`, and `transaction_quantity` into `transaction.item`, `transaction.type`, and `transaction.quantity` merely because they appear in `FUNCTION updateInventory ACCEPTS(inventory, transactions)`. AJ_24038155 Dialect v1.1 permits underscores in identifiers, and the function/parameter/iterator names do not establish member-access structure. Explicit source member access remains unchanged.

GC146's separate `ALERT expression` to `OUTPUT expression` surface recovery remains available. Historical sources that depended on the invented property relationship now correctly reach ordinary declaration-before-use semantics when the flattened identifiers are not otherwise declared. No parser, compiler, intrinsic, or frozen AJ_24038155 Dialect v1.1 semantics change in v3.63.

## v3.62 retire GC159 generic maze-coordinate identifier inference

v3.62 removes GC159's conversion of valid AJ identifiers such as `start_row`, `start_col`, `current_row`, `current_col`, `direction_row`, and `direction_col` into indexed forms such as `start[0]`, `current[1]`, and `direction[0]` merely because a function accepts `(maze, start, end)` and declares `directions`. AJ_24038155 Dialect v1.1 permits underscores in identifiers, and those surrounding names do not establish any particular coordinate representation.

Explicit source indexing remains unchanged. The separate explicit four-direction literal recovery and indexed-assignment token canonicalisation remain available and are independent of the retired naming inference. No parser, compiler, intrinsic, or frozen AJ_24038155 Dialect v1.1 semantics change in v3.62.

## v3.61 retire GC159 generic linked-list flattened-property inference

v3.61 removes GC159's generic conversion of valid AJ identifiers such as `current_next` into member access such as `current.next` merely because `current <- head` appears in a function accepting `head`. AJ_24038155 Dialect v1.1 permits underscores in identifiers, so assignment from `head` plus a `*_next` spelling is not sufficient evidence of object-member structure. Explicit source member access such as `current.next` remains unchanged.

The separately gated Floyd recoveries remain available for the two historical corpus vocabularies `slow`/`fast` and `tortoise`/`hare`. They no longer depend on the retired generic `head` + `*_next` path. No parser, compiler, intrinsic, or frozen AJ_24038155 Dialect v1.1 semantics change in v3.61.

## v3.60 retire GC159 generic binary-tree flattened-property inference

v3.60 removes GC159's generic conversion of valid AJ identifiers such as `node_value`, `node_left`, and `node_right` into `node.value`, `node.left`, and `node.right` merely because the source also contains an identifier named `root`. AJ_24038155 Dialect v1.1 permits underscores in identifiers, and `root` alone is not evidence that `node_*` denotes member access.

The separately gated `LEVEL_ORDER_TRAVERSAL(root)` recovery remains available when `node` is explicitly obtained from `DEQUEUE(queue)`. Its gate now also recognises the already-canonicalised intermediate spelling `node <- REMOVE FIRST ITEM FROM queue`, preserving the intended narrow behaviour after earlier queue normalisation. Explicit source member access is unchanged. No parser, compiler, intrinsic, or frozen AJ_24038155 Dialect v1.1 semantics change in v3.60.

## v3.59 retire GC159 transaction-name flattened-property inference

v3.59 removes GC159's transaction-name-based conversion of valid identifiers such as `transaction_itemID`, `transaction_item`, `transaction_type`, and `transaction_quantity` into member access merely because the source contains `FOR EACH transaction IN transactions`. The iterator and collection names are not independent evidence that those underscored identifiers denote properties of the current transaction object. Explicit member access such as `transaction.itemID` remains unchanged.

The separate GC146 `updateInventory(inventory, transactions)` recogniser is intentionally unchanged in this release and remains independently gated by its existing algorithm-specific evidence. No parser, compiler, intrinsic, or frozen AJ_24038155 Dialect v1.1 semantics change in v3.59.

## v3.58 retire GC159 generic flattened-property inference

v3.58 removes GC159's generic conversion of nested-iterator identifiers such as `item_value` and `otherItem_value` into member access such as `item.value` and `otherItem.value`. AJ_24038155 Dialect v1.1 permits underscores inside identifiers, so the spelling itself is not evidence of object/property structure; likewise, an `otherX` iterator name does not establish that its underscored uses are fields. The generic nested-iterator path now preserves the source identifier; separate specialised object-context recoveries are unchanged by this release.

The existing specialised GC159 object-context recoveries remain unchanged in this release and can be audited independently. Explicit source member access such as `otherItem.value` is preserved. No parser, compiler, intrinsic, or frozen AJ_24038155 Dialect v1.1 semantics change in v3.58.

## v3.57 GC159 self-exclusion retirement

v3.57 removes GC159's automatic insertion of `IF otherItem != item THEN` for nested `otherX` iteration over the same collection. Iterator naming alone is not evidence that the current outer element must be excluded, so compatibility normalisation now preserves the source loop body unless the source itself contains an exclusion condition.

GC159's separate flattened-property surface recovery remains unchanged in this release: forms such as `otherItem_value` may still canonicalise to `otherItem.value` under the existing nested-iteration pattern. Explicit source-written self-exclusion guards are preserved. No parser, compiler, intrinsic, or frozen AJ_24038155 Dialect v1.1 semantics change in v3.57.

## v3.56 retirement of synthetic random input inference

v3.56 retires the obsolete GC119 two-list input synthesis and the synthetic-input portion of GC118. Compatibility normalisation no longer replaces external list inputs with `CALL random_list()` or removes an external matrix input in favour of `CALL random_matrix(N, N)`. Those behaviours were early executable-test conveniences and violate the current evidence rule that normalisation may constrain or canonicalise supplied data structures but must not fabricate arbitrary input data.

External `INPUT` values are now preserved. The independent transpose surface recovery remains unchanged, so explicit `TRANSPOSE Matrix` can still canonicalise to the existing in-place transpose representation without generating matrix contents. The existing compiler intrinsics are not removed because explicit AJ may still invoke them; this release changes only automatic compatibility inference. No parser, compiler, intrinsic, or frozen AJ_24038155 Dialect v1.1 semantics change in v3.56.

## v3.55 evidenced collection query/access dispatch

v3.55 completes the approved semantic tightening for the historical collection query/access rules GC045-GC048.  `.size()`, `.front()`, `.back()`, and `.isEmpty()` are now canonicalised only when the receiver is independently established in readable lexical scope as a compatible list/set/dictionary/queue/deque/stack representation.  Method spelling alone no longer establishes collection type.  The existing meanings and historical GC IDs are preserved; subsequent canonical passes may render `~LENGTH` as `LENGTH OF` and `[LAST]` as `[-1]` as before.

The shared `LexicalEvidenceContext` now also promotes explicit instance-member collection construction from a constructor into the enclosing class evidence frame, for example `self.stack_in = Stack()` or `THIS.items <- EMPTY LIST`.  Sibling methods can therefore consume that proven field type.  Constructor-local variables are not promoted, method-local direct rebinds invalidate inherited evidence only in that method, class scopes remain isolated, and a later constructor does not forward-prove an earlier method.  This restores source_d 40 while retaining the new refusal boundary for unproven calls such as `indexer.front()`.  No parser, compiler, intrinsic, or frozen AJ_24038155 Dialect v1.1 semantics change in v3.55.

## v3.54 source_e 37 class-state composition

v3.54 fixes two composition gaps exposed by the retained source_e algorithm 37 class.  GC241 now accepts both raw `CLASS Name` headers and headers already canonicalised to `CLASS Name ACCEPTS(...)`, so direct-child `Constructor()`/`FUNCTION` routines can still become frozen-AJ `CONSTRUCTOR`/`METHOD` blocks.  The Python compiler also infers instance fields from direct constructor identifier assignments when later class methods reference those same names without parameter shadowing.  This lets constructor state such as `array <- EMPTY LIST` and `top <- -1` compile to `self.array` and `self.top` without rewriting canonical AJ to inject `THIS.`.

The compiler-side inference is deliberately narrow: constructor-only temporaries remain local, method parameters shadow inferred fields in their own method, nested constructor assignments are not promoted, and explicit `PROPERTY`/`THIS` semantics are unchanged.  v3.54 does **not** invent Python list auto-growth.  Therefore source_e 37 now reaches its remaining source-level boundary exactly: `array = []` followed by indexed growth `array[0] = element` raises `IndexError` rather than being silently converted to append/preallocation semantics.

## v3.53 source_a/source_e standing corpus integration

v3.53 adds the two supplied 50-algorithm source_a and source_e research-response exports to the permanent regression corpus under `tests/corpora/`.  Corpus evaluation now decodes source bytes losslessly: UTF-8/UTF-8-SIG is preferred, with Windows-1252 fallback only when the byte stream is not valid UTF-8.  This preserves source characters such as `×` instead of replacing them with U+FFFD.

The new regression gate verifies exact 50-task extraction for both models, excludes source_e `Example:` prose from executable bodies, and runs all 100 items through the normal compatibility processor/parser with parse-rate floors (source_a >= 38/50, source_e >= 45/50).  The floors catch regressions while allowing future evidence-backed improvements.  No pseudocode normalisation, parser, compiler, intrinsic, or frozen AJ_24038155 Dialect v1.1 semantics are changed.

# NL to Flow Diagram Encoder Pipeline v3.64

A dependency-free, object-oriented Python pipeline for AJ_24038155 Dialect v1.1.


## v3.52 evidence-only bare-brace collection resolution

v3.52 retires the historical GC092/GC093 variable-name heuristics for ambiguous bare `{}` initialisers. Identifier spelling such as `seen`, `visited`, `pairs`, `freq`, `counts`, `cache`, or `parent` is no longer treated as collection-type evidence. Bare braces are resolved only when later same-scope structural use proves exactly one compatible interpretation before any direct rebind: indexed access or standard dictionary operations prove dictionary semantics, while standard set insertion proves set semantics. Conflicting evidence, membership/iteration alone, quoted operation text, cross-routine use, and post-rebind operations leave `{}` unresolved. Existing indexed-write evidence retains historical GC220; the general structural-evidence path is recorded as GC250.

The release also adds a permanent internal regression corpus, extracted through the normal source_f corpus adapter, containing the four audited source_f bare-brace examples plus negative cases for weak/ambiguous evidence. This corpus is part of the normal pytest gate so future refactors must preserve both the positive structural proofs and the refusal boundaries. The original external research-response files are not modified. No parser, compiler, intrinsic, or frozen AJ_24038155 Dialect v1.1 semantics change in v3.52.



## v3.51 evidenced simple collection-method dispatch

v3.51 completes the separately approved semantic tightening phase for the historical simple collection-method rules GC033-GC039. Method spelling alone no longer establishes collection semantics: `.append`, `.add`, `.enqueue`, `.dequeue`, `.push`/`.push_back`, `.pop_front`, and `.pop_back` are canonicalised only when the receiver is independently evidenced in readable lexical scope as a compatible list/set/queue/deque/stack representation. The same `LexicalEvidenceContext` introduced in v3.50 now supplies routine/class isolation, inherited enclosing evidence, formal-parameter shadowing, direct-rebind invalidation, and explicit typed-parameter evidence for these rules.

The already-evidenced balanced collection paths GC200, GC202, GC213 and GC221 now consume the same lexical context instead of a source-wide name set. Existing proven corpus cases retain the same processed AJ and historical transformation IDs; a v3.50-v3.51 differential probe confirmed exact identity for representative evidenced list/set/queue/deque/stack cases. The deliberate behaviour change is limited to unproven receivers: for example `obj.append(x)` or `obj.push(x)` is no longer reclassified as an AJ list/stack operation merely from the member name. No parser, compiler, intrinsic, or frozen AJ_24038155 Dialect v1.1 semantics change in v3.51.


## v3.50 generalised structural/evidence rule-set foundation

v3.50 is a behaviour-preserving consolidation release. It introduces shared quote-aware balanced-delimiter scanning, one shared top-level-comma/outer-parenthesis tuple surface implementation, and a shared balanced member-call parser used by the existing evidenced nested collection-operation rules. The duplicated RETURN/OUTPUT tuple splitters now delegate to the same implementation, and GC220 reuses the same balanced-delimiter scanner for nested indexed-write evidence.

A reusable `LexicalEvidenceContext` now owns routine-local or inherited source evidence, parameter shadowing, and direct-rebind invalidation. Existing evidence-gated paths for set-to-list conversion (GC232), post-expansion list-backed queue operations (GC235), deque surface operations (GC237), set tuple insertion evidence collection (GC248), matrix-backed `Copy(...)` (GC247), list/stack and dictionary evidence collection now use this common representation without changing their acceptance criteria. GC246 and GC249 retain separate surface guards and historical rule IDs but share one zero-filled `create_matrix(...)` renderer.

No compatibility spelling, semantic inference, parser rule, compiler lowering, or AJ_24038155 Dialect v1.1 behaviour is added or removed in v3.50. In particular, the older globally permissive simple collection-method rules are intentionally unchanged; tightening those remains a separate semantic phase requiring explicit approval.


## v3.49 nested indexed-write dictionary evidence

v3.49 refines the existing GC220 bare-empty-braces resolution used for source forms such as `seen = {}`. GC220 already promotes a bare `{}` receiver to `EMPTY DICTIONARY` when a later indexed assignment proves mapping semantics; v3.49 extends that evidence check to balanced nested index expressions such as `seen[s[i]] = i` instead of assuming the index contains no `]`. The scanner remains assignment-only and receiver-specific, so indexed reads, `==` comparisons, writes to other receivers, membership-only use, and unrelated expressions do not become dictionary evidence. source_f Algorithm 25 now preserves `seen` as a dictionary and executes the supplied longest-substring algorithm correctly without changing parser/compiler behaviour or frozen AJ_24038155 Dialect v1.1.


## v3.48 explicit rectangular zero-filled matrix recovery

v3.48 adds GC249 for the approved source_d Algorithm 45 allocation spelling `rows x cols matrix filled with 0`. The exact direct-assignment form is represented through the pipeline's existing matrix-construction intrinsic as `CALL create_matrix(rows, cols, 0)`, preserving both source-supplied dimensions and the explicit zero fill. The rule is deliberately narrow: row and column dimensions must each be simple identifiers, the collection noun must be `matrix`, and the fill must be exactly zero; expression dimensions, non-zero or missing fills, `grid` spellings, and prose remain untouched. source_d Algorithm 45 now reaches strict AJ parsing, deterministic Python compilation, and correct rectangular matrix-addition execution without changing frozen AJ_24038155 Dialect v1.1.


## v3.47 evidenced two-value tuple set-insertion recovery

v3.47 adds GC248 for the approved source_d Algorithm 42 source form where an explicitly set-backed receiver is given a parenthesised two-value pair, such as `ADD (MIN(num, complement), MAX(num, complement)) TO pairs`. After the existing set-operation lowering has produced `CALL add_to_set(pairs, (..., ...))`, GC248 renders that explicit pair as the existing AJ `TUPLE(...)` value. The rule requires an `EMPTY SET` evidence declaration and exactly two top-level values inside one outer parenthesis pair; grouped single expressions, unproven receivers, and non-two-value payloads are unchanged. No set, tuple, parser, compiler, or frozen-dialect semantics are added.


## v3.46 evidenced 2D matrix-copy recovery

v3.46 adds GC247 for the approved source_d Algorithm 41 `Copy(board)` operation. When a simple identifier is already evidenced as matrix-backed by `CALL create_matrix(...)` in the current lexical scope or a readable enclosing scope, the exact free one-argument `Copy(name)` form is represented as `CALL copy_2d_list(name)`. Deterministic Python lowering is `list(map(list, name))`, duplicating the outer list and every row so subsequent indexed backtracking mutations do not alter saved board snapshots. The rule refuses unproven values, shadowed parameters, direct reassignments, member calls, wrong arities, comments and quoted text. GC247 composes with GC245/GC246 and makes source_d Algorithm 41 executable without introducing a general deep-copy rule or changing frozen AJ_24038155 Dialect v1.1.

## v3.45 explicit square zero-grid allocation recovery

v3.45 adds GC246 for the approved source_d Algorithm 41 board declaration `N x N grid initialized to 0`. The exact direct-assignment form is represented through the pipeline's existing matrix-construction intrinsic as `CALL create_matrix(N, N, 0)`, preserving the source-supplied square dimensions and zero fill without adding matrix semantics. The rule is deliberately narrow: row and column dimensions must be the same single identifier, the fill must be exactly zero, and rectangular grids, expression dimensions, non-zero fills, missing initialisers and prose remain untouched. GC245's previously approved non-mutating singleton-set recovery composes unchanged with GC246. source_d Algorithm 41 now reaches strict AJ parsing and deterministic Python compilation; its next independent source boundary remains the unresolved explicit `Copy(board)` operation, which v3.45 deliberately leaves visible. Frozen AJ_24038155 Dialect v1.1 is unchanged.


## v3.44 evidenced non-mutating singleton-set extension

v3.44 adds GC245 for the user-approved source_d Algorithm 41 interpretation of expressions such as `cols + {col}` when the corresponding formal parameter is independently evidenced as set-backed by an explicit canonical call supplying `EMPTY SET` in that argument position. The expression is represented without mutation through the existing compatibility intrinsics as `CALL to_set(CALL to_list(cols) + CALL list_value(col))`; analogous diagonal expressions preserve their supplied arithmetic unchanged. Multi-member/dictionary braces, unproven parameters, cross-routine evidence, duplicate routine declarations and member-qualified receivers remain outside the rule. source_d Algorithm 41 therefore advances past its singleton-set syntax to the next independent boundary, the explicit `N x N grid initialized to 0` board allocation, which v3.44 deliberately leaves unchanged. Frozen AJ_24038155 Dialect v1.1 is unchanged.


## v3.43 contextual list-backed Stack() state recovery

v3.43 adds GC244 for the user-confirmed source_d Algorithm 40 interpretation that `Stack()` used as class state denotes a list-backed stack. The rule is evidence-gated: an exact zero-argument constructor member initialiser such as `self.stack_in = Stack()` is represented as `EMPTY LIST` only when that same member is subsequently used through source-supplied stack operations (`push`, `pop`, and/or `isEmpty`) in the class. Simple and nested pushes are routed to the existing AJ `APPEND` representation; existing `pop()` and empty-check lowering are reused unchanged. Local `Stack()` calls, non-zero-argument constructors, state with no stack-use evidence, and directly rebound members are refused. source_d Algorithm 40 therefore reaches strict AJ parsing, deterministic Python compilation, and correct FIFO queue execution using two Python lists without changing frozen AJ_24038155 Dialect v1.1.


## v3.42 member-indexed assignment recovery

v3.42 adds GC242 for the approved source_d Algorithm 37 assignment surface `object.member[index] = value`. The rule changes only the single assignment token to AJ `<-`, preserving the object/member path, index expression, and right-hand value verbatim; `==`, `!=`, `<=`, and `>=` remain untouched. Plain assignments, index-only assignments, and member-only assignments continue through the existing GC026 path. Combined with v3.40's user-confirmed `[None] * capacity` backing-array meaning and v3.41's contextual class-routine recovery, source_d Algorithm 37 now reaches strict AJ parsing, deterministic Python compilation, and correct fixed-capacity stack execution without changing frozen AJ_24038155 Dialect v1.1.


## v3.41 contextual class-routine recovery

v3.41 adds GC241 for the user-confirmed class-context interpretation exposed by source_d Algorithm 37. When the entire source is one explicit `CLASS` that supplies an explicit `CONSTRUCTOR(...)` plus direct-child `PROCEDURE name(...)` and/or `FUNCTION name(...)` routines, those declarations are represented with frozen AJ v1.1 class grammar: `CONSTRUCTOR ACCEPTS(...) ... ENDCONSTRUCTOR` and `METHOD name ACCEPTS(...) ... ENDMETHOD`. Missing routine/class terminators may be closed only at an unambiguous direct-child routine boundary, an explicit class terminator, or end-of-source. The rule does not invent properties, change `self`/member semantics, repair assignments, or alter return behaviour. Existing classes without an explicit constructor remain on their prior GC203/expected-failure paths. The generic call-prefix and functionless-return wrapper were also constrained so canonical `METHOD`/`CONSTRUCTOR` declarations are not rewritten as calls and a top-level `CLASS` is not wrapped merely because its methods contain `RETURN`. source_d Algorithm 37 therefore advances to its next independent boundary: the legacy member-index assignment `self.arr[self.top_index] = item` is still left visible and is not repaired by v3.41.

## v3.40 user-confirmed NONE-filled fixed-array preallocation

v3.40 adds GC240 for the exact unfilled declaration `Array of size N`, under the project rule explicitly approved during the source_d Algorithm 37 audit: the phrase denotes N writable slots initialised to `NONE`. The compatibility surface is `CALL create_array(N, NONE)`, reusing the existing array-construction intrinsic without changing frozen AJ v1.1 syntax. For a NONE fill, deterministic Python lowering is `[None] * N`; declarations that already specify an initial value remain under the existing GC160 behaviour. GC240 is deliberately restricted to a single identifier or non-negative integer size and refuses broader/qualified size prose. source_d Algorithm 37 therefore now has an explicit backing-array representation, while its remaining legacy class-surface issues are kept separately visible rather than silently bundled into this rule.

## v3.39 explicit set-conversion intrinsic recovery

v3.39 adds GC238 for the exact free single-argument call `ConvertToSet(value)`. The source-explicit conversion is represented through the existing `CALL to_set(value)` compatibility intrinsic, which lowers deterministically to Python `set(value)`. Routine declarations named `ConvertToSet`, member methods, quoted text, comments, and zero/multi-argument calls remain outside GC238. source_d Algorithm 34 therefore preserves its supplied list-to-set conversion while the existing GC232 recovery continues to represent its independently evidenced set-to-list conversion. No parser, compiler, collection semantics, or AJ_24038155 Dialect v1.1 syntax is added.

## v3.38 evidenced deque surface-operation recovery

v3.38 adds GC237 for standalone `REMOVE FRONT FROM receiver`, `REMOVE BACK FROM receiver`, and `ADD BACK value TO receiver`/intermediate `APPEND BACK value TO receiver` forms when that receiver has been explicitly initialised as `EMPTY DEQUE` in the same lexical routine. The operations map only to the existing AJ list primitives `REMOVE FIRST ITEM FROM`, `REMOVE LAST ITEM FROM`, and `APPEND ... TO ...`. Evidence is routine-local and is invalidated by direct reassignment; unproven receivers are untouched. source_d Algorithm 28 therefore preserves its source-supplied double-ended-queue operations after v3.37's comment fix without adding deque syntax or changing AJ_24038155 Dialect v1.1.

## v3.37 early inline `//` comment detachment

v3.37 adds GC236 so text following an unquoted `//` is detached from the executable portion of the line before declaration, literal, and collection compatibility interpretation. The detached text remains in the source stream and is later represented as ordinary non-executable `COMMENT` metadata. This allows a declaration such as `deque = empty DoubleEndedQueue // Stores indices` to expose the complete `empty DoubleEndedQueue` initialiser to the existing collection rules instead of letting the comment contaminate type recovery. `//` inside quoted string literals is preserved as literal data, and standalone `// ...` lines continue through the existing comment path. No deque operations, parser features, or AJ_24038155 Dialect v1.1 syntax are added.

## v3.36 post-expansion evidenced queue-operation recovery

v3.36 adds GC235 as a narrow composition repair for queue operations exposed only after structural one-line conditional expansion. When the same lexical routine has already established a receiver as list-backed (`EMPTY LIST` or the existing `list_value(...)` representation), a newly standalone `ENQUEUE value TO receiver` is routed to the existing AJ `APPEND value TO receiver` operation; the equivalent evidenced free-call form and assignment-form dequeue counterpart share the same guard. Cross-routine evidence, unproven receivers, and receivers invalidated by direct reassignment are refused. source_d Algorithm 26 therefore preserves its explicit child enqueue operations after GC132 expansion without adding queue semantics, parser features, or any AJ_24038155 Dialect v1.1 change.

## v3.35 explicit character-predicate intrinsic recovery

v3.35 adds GC234 for the exact free single-argument calls `IS_DIGIT(value)` and `IS_UPPERCASE(value)`. These source spellings are represented through the existing compatibility intrinsics `CALL is_digit(value)` and `CALL is_uppercase(value)`, which lower deterministically to Python `str(value).isdigit()` and `str(value).isupper()`. Routine declarations, member methods, quoted-text matches, and zero/multi-argument calls are outside GC234. source_d Algorithm 24 therefore preserves its explicit password character tests without adding new predicate semantics or changing AJ_24038155 Dialect v1.1.

## v3.34 explicit square-root representation recovery

v3.34 adds GC233 for the exact free single-argument call `SQUARE_ROOT(value)`. With the user-approved mathematical representation, the source operation is canonicalised to AJ v1.1 exponentiation as `(value EXP 0.5)`, which lowers deterministically to Python `(value ** 0.5)`. Routine declarations named `SQUARE_ROOT`, member methods, quoted text, and zero/multi-argument calls are refused. GC233 deliberately does not add integer, floor, or range-bound coercion. source_d Algorithm 20 therefore now preserves its explicit square-root operation through strict AJ parsing and Python compilation, while its separate use of that floating result as a Python range endpoint remains visible as an executable-correctness boundary. AJ_24038155 Dialect v1.1 remains frozen.

## v3.33 evidenced set-to-list conversion recovery

v3.33 adds GC232 for the exact free call `ConvertSetToList(name)` when the same lexical routine has already established `name` as `EMPTY SET` and no later direct reassignment invalidates that evidence. The explicit conversion is represented through the existing `CALL to_list(name)` compatibility intrinsic, which lowers deterministically to Python `list(name)`. Cross-routine evidence, forward evidence, member calls, wrong arity and unproven identifiers are refused. source_d Algorithm 11 therefore preserves its supplied set-deduplication followed by set-to-list conversion without changing AJ_24038155 Dialect v1.1.

## v3.32 quoted dictionary-key recovery

v3.32 refines the existing GC097 simple dictionary-literal expansion so explicitly quoted string-scalar keys are rendered directly as canonical AJ `STRING(...)` expressions before the expanded indexed assignments are returned. This preserves source_d Algorithm 10's source-evidenced vowel keys (including normal AJ escaping) while keeping the established bare-key stringification unchanged. No dictionary semantics are inferred beyond the existing GC097 literal expansion, and AJ_24038155 Dialect v1.1 remains frozen.

## v3.31 quoted scalar set-literal recovery

v3.31 adds GC231 for a non-empty Python-style brace literal whose members are all explicitly quoted string scalars. The source-evidenced set is represented through the existing compatibility intrinsics as `CALL to_set(CALL list_value(...))`, preserving punctuation characters including escaped apostrophe and double-quote members without changing the frozen AJ parser. The rule runs before raw-string wrapping and refuses dictionaries, empty braces, mixed or unquoted members, comprehensions, and string scalars containing unsupported control characters. source_d Algorithm 5 therefore reaches the frozen AJ parser and deterministic Python compilation without inventing a punctuation predicate or changing AJ_24038155 Dialect v1.1.

## v3.30 standalone SWAP boundary fix

v3.30 narrows GC051 to the standalone procedural shorthand `SWAP(a, b)` only. A case-sensitive routine declaration such as `FUNCTION swap(a, b):` is therefore left for the ordinary function-header recovery and preserves the source identifier as `swap`, while genuine standalone `SWAP(a, b)` statements continue through the existing SWAP lowering. Calls such as `CALL swap(a, b)` and member invocations such as `obj.swap(a, b)` are also outside GC051. No new compatibility meaning is introduced, and AJ_24038155 Dialect v1.1 remains frozen.
The only external program input is AJ pseudocode.

## Pipeline

1. AJ pseudocode input
2. Lexical analysis
3. Recursive-descent parsing
4. AST construction
5. Static semantic validation
6. Machine-readable flow-diagram encoding
7. Interactive AST and flow-diagram visualisation
8. Deterministic Python compilation from `flow_diagram.json`
9. Subprocess-based behavioural testing
10. JSON reporting

## PyCharm

Open `pycharm_runner.py` and press **Run**. Configure these constants at the top
of the file when required:

- `INPUT_FILE`
- `OUTPUT_DIRECTORY`
- `OPEN_VISUALISATIONS`
- `TEST_CASES`

## Outputs

The runner creates:

- `output/ast.json`
- `output/parser_report.json`
- `output/ast_visualisation.html`
- `output/flow_diagram.json`
- `output/flow_diagram.html`
- `output/generated_program.py`
- `output/compilation_report.json`
- `output/test_report.json`
- `output/pipeline_report.json`

## Important design boundary

The AST is an internal intermediate representation. It is generated from
pseudocode and is not accepted as an external pipeline input. The compiler
accepts the machine-readable flow-diagram document produced by the encoder.


## v3.29 chained-assignment negative-infinity pass-order fix

v3.29 fixes the composition of the existing GC079 chained-assignment expansion with the existing GC151 negative-infinity representation recovery. When source such as `largest <- second <- -INFINITY` is expanded, the newly exposed assignment is now canonicalised as `second <- CALL negative_infinity()` before `largest <- second`. This preserves the source-supplied shared negative-infinity initialiser and lowers deterministically to Python `float('-inf')`. The fix is deliberately limited to the negative-infinity surfaces already accepted by GC151; positive infinity identifiers, member properties, and arbitrary chained right-hand expressions are unchanged. No new compatibility meaning is introduced, and AJ_24038155 Dialect v1.1 remains frozen.

## v3.28 direct modulus-digit string-accumulator recovery

v3.28 adds GC230 for the exact representation case where a destination is explicitly string-backed, the source directly prepends one parenthesised `MOD`/`MODULUS` result to that same accumulator, and the later generic arithmetic canonicalisation has not yet rewritten `MOD` to `MODULUS`. The guarded recovery makes only the required digit-to-string representation explicit as `CALL to_string((... MODULUS ...))`; unrelated mixed numeric/string addition, different accumulators, non-string destinations, and non-modulus expressions remain untouched. source_b Algorithm 2 therefore compiles without changing its supplied decimal-to-binary algorithm. AJ_24038155 Dialect v1.1 remains frozen.

## v3.27 seeded list-backed queue recovery

v3.27 adds GC229 for source forms that explicitly initialise a queue receiver from a non-empty list literal (for example `queue = [root]`) and then explicitly use that same receiver with free `DEQUEUE(queue)` / `ENQUEUE(queue, value)` operations. The earlier list-literal canonicalisation is accepted as representation evidence, and the queue operations are routed only to the existing list-backed FIFO operations (`REMOVE FIRST ITEM FROM` / `APPEND`). Unproven receivers, unrelated seeded lists, and arbitrary queue-like names remain untouched. AJ_24038155 Dialect v1.1 remains frozen.

## v3.26 explicit alphabetical sort-mode recovery

v3.26 adds GC228 for the exact free two-argument form `SORT(value, ALPHABETICAL_ORDER)`. The explicit `ALPHABETICAL_ORDER` marker is treated as source-supplied ascending alphabetical ordering and routed through the existing `sort_value` compatibility intrinsic, which lowers to Python `sorted(value)` (equivalent to `sorted(value, reverse=False)`). The rule is restricted to a simple identifier first argument and leaves arbitrary comparators, descending markers, member methods, and other arities untouched. AJ_24038155 Dialect v1.1 remains frozen.

## v3.25 evidenced regex `REPLACE_ALL` recovery

v3.25 adds GC227 for free three-argument `REPLACE_ALL(text, pattern, replacement)` calls whose quoted pattern contains direct regular-expression syntax evidence. The rule protects regex backslashes across compatibility-to-AJ string representation and lowers the supplied operation through an internal `regex_replace` intrinsic backed by Python `re.sub`. Plain literal replacement calls, member methods, and other arities remain untouched. AJ_24038155 Dialect v1.1 remains frozen.

## v3.24 trailing explanatory parenthetical comment recovery

v3.24 adds GC226 for a narrowly guarded source-surface case where an assignment already has a complete `empty <collection>` right-hand side and is followed by a trailing parenthetical beginning with explanatory `or` or `for` prose. The suffix is detached from executable syntax before literal/collection parsing, so a line such as `order = empty list (or a doubly linked list to maintain access order)` is represented as the explicit empty-list initialiser plus non-executable commentary rather than being misread as a `list(...)` constructor. Arithmetic/grouping parentheses, arbitrary calls, and non-comment parentheticals are unchanged. The existing source_c LRU class recovery also accepts its legacy `FUNCTION get(key):` / `FUNCTION put(key, value):` header surface, allowing the already source-evidenced LRU logic to reach the frozen class grammar without inventing cache behaviour. AJ_24038155 Dialect v1.1 remains frozen.

## v3.23 source_c 2 source-evidenced numeric STRING conversion

v3.23 adds GC225 for the exact compatibility case where a variable is independently proven numeric by a `MOD`/`MODULUS` assignment, a destination is independently proven string-backed by `EMPTY STRING`, and the source explicitly prepends `STRING(variable)` to that same string accumulator. Under those safeguards, the non-literal constructor-like source form is represented as `CALL to_string(variable)`, which lowers through the existing Python intrinsic to `str(variable)`. Quoted `STRING("...")` literals, unproven identifiers, non-string destinations, and unrelated `STRING(...)` calls are unchanged. source_c Algorithm 2 therefore preserves its supplied decimal-to-binary algorithm while making only the explicit numeric-to-text conversion executable. AJ_24038155 Dialect v1.1 remains frozen.

## v3.22 source_f 46 source-evidenced linked matrix dimensions

v3.22 adds GC224 for the exact matrix-multiplication shape `INPUT A (M x N), B (N x P)` followed by `INIT C as M x P matrix`, the complete nested `M`/`P`/`N` loops, the explicit `sum += A[i][k] * B[k][j]` accumulation, direct `C[i][j] = sum`, and `RETURN C`. Under those safeguards, annotation-only `M`, `N`, and `P` are represented by `LENGTH OF A`, `LENGTH OF B`, and `LENGTH OF B[0]`; `C` is materialised with the existing `create_matrix` intrinsic. The rule refuses independently bound dimensions, mismatched result or loop shapes, altered accumulation/index relations, conditional result writes, dimension-symbol escape, and explicit routine declarations. No matrix-multiplication logic or synthetic dimension parameter is invented. AJ_24038155 Dialect v1.1 remains frozen.

## v3.21 source_f 45 source-evidenced rectangular matrix recovery

v3.21 adds GC223 for the exact unnamed matrix-addition shape where two supplied matrices are explicitly annotated as sharing dimensions `R x C`, the source requests `INIT result as R x C matrix`, the matching nested `0..R-1` / `0..C-1` loops directly overwrite every `result[i][j]`, and the result matrix is returned. Under those safeguards, annotation-only `R` and `C` are represented by `LENGTH OF A` and `LENGTH OF A[0]`, and the result storage is materialised with the existing `create_matrix` intrinsic. No synthetic `R`/`C` parameters are introduced. The zero fill is permitted only because the guarded source shape proves every allocated cell is overwritten before observation. Independent dimensions, mismatched bounds, conditional writes, explicit routine declarations, and non-returned targets are refused. AJ_24038155 Dialect v1.1 remains frozen.

## v3.20 source_f 42 collection-evidence and deduplication recovery

v3.20 adds three narrowly evidenced compatibility recoveries for the source_f 42 pair-sum form. A bare `{}` declaration is resolved to `EMPTY DICTIONARY` when a later indexed assignment on the same receiver proves mapping use (GC220), overriding weaker identifier-name set hints. A nested `list.add(expression)` is recovered with balanced-parenthesis scanning only when the receiver is independently proven list-backed (GC221); the recovered expression then continues through the existing tuple/MIN/MAX canonicalisation passes. Finally, after the stronger GC214 proof-based redundant-uniqueness rule has had first priority, an exact remaining one-argument `unique(name)` call is represented by the existing `to_set` compatibility intrinsic (GC222), producing Python `set(name)`. No pair-search logic is invented, ordering is not inferred, and AJ_24038155 Dialect v1.1 remains frozen.

## v3.19 guarded RANGE integer-offset folding

v3.19 broadens the v3.18 Python RANGE rendering cleanup into a guarded additive-integer offset fold. Within RANGE end expressions only, two or more literal integer offsets on the same left-associated `+`/`-` chain are combined while non-literal terms retain their relative order. Examples include `(Limit - 2) + 1 -> Limit - 1`, `(Index + 3) - 1 -> Index + 2`, `(Value - 4) - 2 -> Value - 6`, `(Value + 2) - 2 -> Value`, and `((LENGTH OF xs - 2) - i) + 1 -> LENGTH OF xs - 1 - i` at Python rendering time. Single-offset expressions, floats, multiplication/division, and nested right-hand additive algebra are not reassociated. AJ_24038155 Dialect v1.1 remains frozen.

## v3.18 evidenced input/helper wrapper recovery and canonical range rendering

v3.18 adds guarded GC219 for an omitted neutral outer algorithm wrapper when generic pseudocode supplies one or more bare top-level `INPUT` declarations, one or more complete indentation-style helper routines, and a single final top-level `RETURN` that calls an explicitly supplied helper. The recovery promotes only the input names to `FUNCTION unnamed_function` parameters and nests the supplied helpers/return without implementing any missing dependency. source_f Algorithm 41 therefore parses and compiles structurally, while its undefined `isSafe(...)` and `emptyBoard(...)` routines remain source-level expected-failure dependencies. v3.18 also makes Python RANGE rendering cleaner: when inclusive-source endpoint canonicalisation has produced exactly `(X - 1) + 1`, the Python compiler emits `X` in the `range()` stop position (for example `0 TO N - 1` now renders as `range(0, N)`). This cancellation is restricted to RANGE end expressions and is not a general arithmetic optimiser. AJ_24038155 Dialect v1.1 remains frozen.

## v3.17 evidenced connected multi-list stateful-ADT recovery

v3.17 adds guarded GC218 structural recovery for multiple explicitly initialised `EMPTY LIST` states followed by multiple top-level operations. The rule requires the complete state/operation graph to be connected, every state to be actively mutated, and at least one explicit destructive cross-state transfer such as `APPEND a.pop() TO b`; it also refuses unknown call escape, state shadowing, direct rebinding, indexed writes, nested functions, free executable statements and disconnected global-list utilities. Eligible source is represented as neutral `CLASS unnamed_class` with a zero-argument constructor containing only the source-supplied empty-list initialisers. source_f Algorithm 40 therefore becomes a trustworthy executable stateful queue abstraction while preserving its source-supplied empty-dequeue underflow. AJ_24038155 Dialect v1.1 remains frozen.

## v3.16 evidenced counted-list stateful-ADT and standalone-error recovery

v3.16 adds guarded GC216 structural recovery for an explicitly initialised counted-list ADT written as top-level state plus multiple shared-state functions. The rule requires exactly one `EMPTY LIST` state and one zero counter, at least three operations that all share both values, and source evidence for append, zero-argument list `pop()`, indexed top access, and counter `+1`/`-1` updates. Eligible source is represented as neutral `CLASS unnamed_class` with a zero-argument constructor containing only the supplied initial values; no semantic class name, constructor parameter, stack operation, or data value is invented. v3.16 also adds GC217 for an exact standalone `ERROR` statement, mapping it to AJ `RAISE STRING("ERROR")`. GC217 is statement-position only and leaves the established GC204 `RETURN ERROR` string-sentinel policy unchanged. source_f Algorithm 37 therefore becomes a trustworthy executable without changing AJ_24038155 Dialect v1.1.

## v3.15 evidenced ordered-cache stateful-ADT recovery

v3.15 adds guarded GC215 recovery for the source shape `INIT limit, cache = orderedDict()` followed by multiple top-level operations that share the ordered key/value state. The rule activates only when the same source proves a cache-size bound (`LENGTH OF cache == limit`), keyed membership/indexing, and safe recency-helper contexts: move-to-front only for a present key, remove-back only under the full-capacity guard, and add-to-front only in the absent-key branch. The first INIT name becomes a constructor-supplied property rather than receiving a synthetic numeric default; the ordered cache becomes an AJ `DICTIONARY` property, and existing ordered-mapping compiler intrinsics provide the physical MRU/LRU lowering. The recovered wrapper is the neutral `unnamed_class`, so no semantic class name is invented. source_f Algorithm 35 therefore becomes a trustworthy executable for positive fixed capacities without changing AJ_24038155 Dialect v1.1.

## v3.14 provable redundant-uniqueness alignment

v3.14 adds guarded GC214 semantic alignment for a final `RETURN unique(result)` abstraction only when the same routine mechanically proves that `result` is already unique: the collection is explicitly initialised as `EMPTY LIST`, every append is protected by a matching `value NOT IN result` guard that is re-evaluated before that append, and no rebinding, indexed/insert mutation, alias/call escape, repeated append under one guard, or nested-loop bypass invalidates the proof. The alignment preserves the source-created order by returning `result` directly; it does not implement a generic `unique` routine or rewrite arbitrary `unique(x)` calls. source_f Algorithm 34 therefore becomes a trustworthy executable after source-proven semantic alignment. AJ_24038155 Dialect v1.1 remains frozen.

## v3.13 bare CALL-argument binding validation

v3.13 extends the frozen AJ v1.1 declared/assigned-before-read check to immediate bare value identifiers supplied as arguments to `CALL routine(...)`. Routine names remain syntax and are not treated as value reads, undefined external-routine policy is unchanged, and compound-expression definite-assignment analysis remains deliberately out of scope. source_f Algorithm 30 now fails during static semantic analysis on the unbound `numTopics` argument instead of producing executable-looking Python with a latent `NameError`. Its abstract NLP/LDA routine dependencies remain source-level expected failures. AJ_24038155 Dialect v1.1 remains frozen.

## v3.12 evidenced camelCase deque-operation recovery

v3.12 adds guarded GC213 compatibility recovery for source_f-style `popFront()`, `popBack()`, and `pushBack(value)` calls when the receiver is independently established as list-backed in the same source. The rule maps directly to the existing AJ list operations `REMOVE FIRST ITEM FROM`, `REMOVE LAST ITEM FROM`, and `APPEND ... TO ...`; arbitrary user-defined methods with the same names are not rewritten. source_f Algorithm 28 still retains its source-level empty-deque indexing defect and is audit-locked as an expected executable-correctness failure. AJ_24038155 Dialect v1.1 remains frozen.

## v3.11 square-dimension identifier-reference recovery

v3.11 adds generic GC212 compatibility recovery for otherwise-unbound executable references to a dimension symbol explicitly established by `INPUT collection (D x D)`. The symbol resolves directly to `LENGTH OF collection` within the same routine, without creating a synthetic `D` variable. GC208 retains its exact `0 .. D-1` loop-bound ownership. Arithmetic is preserved exactly: source_f Algorithm 27 now eliminates unbound `N`, but its source `N / 2` remains ordinary division and is audit-locked as an expected executable-correctness failure rather than silently corrected to integer division. AJ_24038155 Dialect v1.1 remains frozen.

## v3.10 omitted-`IS` non-empty predicate recovery

v3.10 adds generic GC211 compatibility recovery for the exact surface `identifier NOT EMPTY`, mapping it to the already-supported canonical empty-state test `LENGTH OF identifier > 0`. The rule is case-insensitive, quote/comment-safe, and deliberately does not broaden to blank/null/whitespace/missing predicates or member expressions. source_f Algorithm 26 now passes without inventing tree semantics. AJ_24038155 Dialect v1.1 remains frozen.

## Research corpus and audit evidence

The complete six model-response corpora used for the research study remain external
study data and are not copied wholesale into versioned implementation ZIPs.
Study-level corpus integration checks can be run by setting `AJ_RESEARCH_CORPUS_DIR`
to an external directory containing those files. When that variable is absent,
corpus-dependent checks skip cleanly.

When an exact study occurrence motivates a general parsing or normalisation measure,
that occurrence may be retained as a focused regression fixture together with its
audit record. These selected cases are version-controlled evidence for why the
measure was introduced; they are distinct from bundling the complete research corpus.

## Flow-diagram display

The generated flowchart opens at a readable 115% scale and is centred on the
first program steps. Use **Fit diagram** to display the complete program at once.
Zoom and pan remain available.

## Compilation assurance tests

The integration tests verify that:

- the saved `flow_diagram.json` document is accepted directly by the compiler;
- the compiler produces the exact expected reference Python source;
- the compiled program executes and produces the expected output;
- the visualisation contains the readable initial-view configuration.

Run all tests with:

```bash
python -m unittest discover -s tests -v
```

## Second controlled input route: draw.io

Version 1.5 adds an optional draw.io route while preserving pseudocode as the
primary route.

Configure `pycharm_runner.py` with:

```python
INPUT_ROUTE = "DRAWIO"
SELECT_FILE_WHEN_RUNNING = True
```

The runner displays a native file chooser. The controlled version 1 convention
is deliberately limited to a single linear path:

```text
Start -> AJ statement -> AJ statement -> End
```

Each executable process or input/output shape must contain one valid AJ Dialect
statement, either directly or with an `AJ:` prefix, for example:

```text
AJ: total <- INTEGER(0)
AJ: OUTPUT STRING("Total is {total}")
```

The importer reconstructs AJ pseudocode and then reuses the existing trusted
route:

```text
draw.io -> AJ pseudocode -> AST -> canonical flow JSON -> Python -> tests
```

Branching and looped draw.io imports intentionally fail with explicit diagnostics
in this first controlled version. The existing pseudocode route continues to
support the full parser grammar.

## Interactive input selection in PyCharm

Run `pycharm_runner.py` without editing an input-route flag.

The application first asks:

```text
What would you like to import?

[Pseudocode file]
[Flow diagram file]
```

After the selection, a native file chooser opens with the matching filters:

- Pseudocode: `.aj` or `.txt`
- Controlled flow diagram: `.drawio`, `.xml` or `.svg`

Closing either dialog cancels the run cleanly.

## Pseudocode processing profiles

When **Pseudocode file** is selected in `pycharm_runner.py`, the application now
asks how the source should be processed:

1. **AJ Dialect — strict** performs only non-semantic cleanup such as removing a
   surrounding Markdown fence, normalising line endings, removing trailing
   whitespace and converting `←` to `<-`.
2. **Generic — convert compatible syntax** recognises a controlled subset of
   generic structured pseudocode and converts forms such as `SET x TO value`,
   `PRINT value`, `END IF`, `END WHILE`, `NEXT`, assignment `=`, `MOD` and `DIV`
   into AJ_24038155 Dialect syntax.
3. **General — parse without conversion** passes the supplied text to the
   existing lexer and parser exactly as read from the file. It does not repair,
   normalise or rewrite the source.

Every pseudocode run writes:

- `processed_pseudocode.aj`
- `pseudocode_processing_report.json`

The report records the selected profile, whether the source changed, and every
individual transformation. The selected profile is also included in
`pipeline_report.json` under `input_metadata`.

## Draw.io overlaid labels

Version 1.8 recognises draw.io diagrams where visible `Start` and `End` text is
stored as a separate text object placed over an empty connected terminator
shape. The importer transfers the text to the underlying shape before graph
validation. Branching and loop-back import remain outside the controlled linear
importer and are rejected explicitly.

## General draw.io control-flow graphs

The draw.io route supports both linear diagrams and general graphs containing:

- decision diamonds;
- Yes/No and True/False connector labels;
- branch joins;
- loop-back connectors;
- separate text labels over Start and End shapes.

Linear diagrams are reconstructed as AJ Dialect pseudocode and use the normal
AST pipeline. Branching or cyclic diagrams are preserved as a canonical graph
and compiled into a Python state machine. This allows control flow that cannot
be represented safely as a simple nested block structure to remain executable.

When no behavioural test oracle is supplied for an imported flow diagram, the
pipeline reports behavioural testing as `SKIPPED` after successful compilation
and Python syntax validation. This avoids comparing an imported diagram against
unrelated sample outputs.

## Version 1.10: structured Tic-Tac-Toe graph compilation

The supplied Tic-Tac-Toe draw.io graph is recognised as a structured game-flow
pattern. It is compiled into a normal Python game loop instead of a verbose
state dispatcher. The generated program validates indexes and occupied cells,
alternates players, checks all eight winning lines, declares the correct winner,
and declares a draw after nine valid moves.

The compiler reports this route as `STRUCTURED_GRAPH_OPTIMISATION`. Other
arbitrary cyclic draw.io graphs continue to use the general state-machine
compiler.

## Flow-diagram input AST outputs

When an existing draw.io flow diagram is selected, the pipeline does not create a duplicate flow-diagram visualisation. After compilation it parses the generated Python into a Python AST and writes:

- `ast.json` — nested Python AST document;
- `ast_adjacency_list.json` — graph representation of the AST;
- `ast_visualisation.html` — interactive AST tree;
- `generated_program.py` — compiled Python source.

The pseudocode input route continues to generate both AST and flow-diagram artefacts.

## Editable draw.io export

The pseudocode input route also writes `output/flow_diagram.drawio`. This is an
editable diagrams.net/draw.io XML document using standard terminator, process,
decision, input/output, subroutine, and orthogonal connector conventions.

## Initial hash-comment header stripping

Before the selected pseudocode profile is applied, the pipeline checks whether the first line begins with `#`. When it does, all lines from the beginning of the file through the first blank separator line are treated as file-header metadata and removed. This supports wrapped introductory comments where continuation lines do not themselves begin with `#`.

Example:

```text
# Algorithm description
This description may wrap across several lines.
These lines are header metadata.

FUNCTION example ACCEPTS()
    OUTPUT STRING(example)
ENDFUNCTION
```

Only the pseudocode beginning with `FUNCTION` is sent to the selected profile and parser. Hash characters occurring later in the pseudocode do not trigger this preprocessing rule. The processing report records `header_comment_removed` and `header_lines_removed` separately from profile transformation counts.

## Lossy-source assignment recovery boundary

The generic compatibility route may receive study/source exports in which a
Unicode assignment arrow was lost as ASCII `?`. This is handled only in the
upstream source-integrity stage (GC193), where `?` is recoverable to source `←`
only when its syntactic position is unambiguously an assignment: a standalone
assignment target, a `FOR` initialiser, or an inline CASE-arm assignment.

`?` is **not** AJ syntax and is never a canonical alias for `<-`. Relational
forms such as `WHILE B ? 0` or `IF A ? B THEN` are left unresolved unless an
entry in the evidence-backed lossy-glyph lookup table establishes the original
source glyph from a recognised full source signature. Table recoveries are
logged as `GC194:<evidence-id>` and restore source glyphs such as `≠`, `≤`, or
`≥`; the deterministic character lookup then maps those glyphs to strict AJ
operators (`!=`, `<=`, `>=`). There is deliberately no `?` entry in the
canonical character lookup. The strict AJ parser continues to reject `?`.

### Working-tree semantic audit note — source_d Algorithm 41 set `+` interpretation

The current audit records the evidence boundary for GC245 in `docs/source_d_algorithm41_set_plus_as_add_audit.md`: source_d Algorithm 41's `cols + {col}` / diagonal variants are accepted as non-mutating SET ADD/extension because the matching recursive parameters are independently evidenced by `EMPTY SET` call arguments and the right operands are singleton sets. This is explicitly **not** a generic `+ -> ADD/UNION` rule; unproven, multi-member, dictionary-shaped, cross-routine, ambiguous, or member-qualified cases remain outside GC245.

## Automatic study dashboards (v4.35 RC9)

Study batch completion now creates presentation dashboards automatically from the
already-written study artefacts. Dashboard generation is strictly downstream of
scoring and cannot alter semantic results, baseline calibration, rubric scores,
or frozen Common Test expectations.

For an LLM-results batch the pipeline writes:

- `study_analysis/dashboards/NL_FDEP_batch_dashboard.html` — one interactive
  50-algorithm dashboard for the completed agent, including behavioural scores,
  Common Test context, Semantic Boundary Variance, rubric fields, assessed
  pseudocode, generated Python, and local-file-safe Copy controls;
- `<study-root>/analysis/dashboards/NL_FDEP_comparative_dashboard.html` — the
  canonical comparative 50-algorithm heat map and behavioural ranking regenerated
  from all completed sibling LLM datasets discoverable under the same study root.
  This is the only generated comparative heat-map HTML; the former
  `NL_FDEP_interactive_heatmap_dashboard_v5.html` duplicate is no longer written.

Baseline batch completion also writes a batch calibration dashboard, but baseline
results are deliberately excluded from the experimental comparative-agent rows.

Dashboard generation is non-blocking. If the presentation layer fails, the batch
remains scientifically valid and `study_analysis/dashboard_generation.json`
records the failure reason. Successful dashboard files and the status record are
copied into the batch `run_history` snapshot.

### v4.37 baseline resume compatibility

An already-current v4.36 baseline does not need to be recalibrated solely because the package version is now v4.37. Resume compatibility is granted only when the source pseudocode, reference Python, Common Tests, rubric, dependency environment and strict baseline profile still match and the canonical flow graph contains no legacy `COMMENT` node. If a legacy comment node is detected, only that affected algorithm is regenerated; comment-free baseline algorithms retain the fast `SKIPPED_CURRENT` path.

