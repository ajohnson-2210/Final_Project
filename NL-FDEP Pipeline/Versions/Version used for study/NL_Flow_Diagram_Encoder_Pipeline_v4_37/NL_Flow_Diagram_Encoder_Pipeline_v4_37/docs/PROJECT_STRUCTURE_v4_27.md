# NL-FDEP v4.27 project structure

The grouped project layout is unchanged. v4.27 corrects the behavioural oracle execution contract while retaining Strict benchmark processing and the packaged Common Tests v1.1 resource layer.

## Key v4.27 controls

- `pycharm_runner.py` — Baseline Benchmark Folder processing remains fixed to `AJ_DIALECT_STRICT`; experimental profiles remain independently selectable.
- `study components/baseline_benchmark.py` — creates a controlled, non-mutating executable view of trusted baseline Python; exact packaged `algorithm_title` headings may be commented only for execution; invalid/non-error runtime faults fail closed as behavioural oracles.
- `compiler components/aj_python_compiler.py` — lowers recognised Strict AJ `LOWERCASE`, `UPPERCASE`, and `CHARACTERS_OF` intrinsics to executable Python and lowers `QUIT`/`STOP` to deterministic `SystemExit`.
- `compiler components/aj_test_harness.py` — supports an explicit working directory for temporary reference execution views while preserving isolated subprocess execution.
- `study components/study_batch.py` — passes packaged suite title metadata into trusted-reference validation/oracle execution without modifying the selected baseline folder.
- `study data/common tests v1.1/` — unchanged packaged 50-suite / 113-test common behavioural resource pack.
- `docs/common_test_design_v1_1.md` and `docs/common_test_suite_manifest_v1_1.json` — unchanged test semantics.
