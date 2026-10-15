# Bundled Common Tests v1.1

NL-FDEP v4.23 resolves the common behavioural test specification for each algorithm from this packaged resource directory and virtually associates it with whichever compatible Baseline benchmark folder is selected at runtime. The selected baseline is not modified.

This release contains **50 JSON suites / 113 behavioural tests**, using **Common Test Design v1.1** and test-spec schema **v1.2**.

The executable `tests` arrays are retained from the supplied Common Tests v1.0 pack. Test Design v1.1 changes only descriptive G2 metadata: evidence summary, six coverage dimensions, coverage basis, interpretation guidance and limitations. The conversion is recorded in `docs/common_test_resource_build_v4_23.json`, including per-algorithm canonical test-array hashes proving semantic equality before and after enrichment.

Resource layout:

- `Algorithm - 1/Algorithm 1 Tests.json`
- ...
- `Algorithm - 50/Algorithm 50 Tests.json`

Packaged common tests take precedence over baseline-local `Tests.json` files. Baseline-local files remain supported only as a backward-compatible fallback if a packaged suite is unavailable.
