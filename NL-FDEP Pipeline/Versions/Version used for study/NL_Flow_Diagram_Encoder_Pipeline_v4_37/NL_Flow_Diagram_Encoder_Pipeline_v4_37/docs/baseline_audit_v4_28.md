# NL-FDEP v4.28 frozen-baseline audit

This audit records the evidence used to scope v4.28. The externally supplied frozen Baselines corpus is **not bundled** and no benchmark source/reference file is modified by the release.

## v4.27 observed baseline calibration

Under `AJ_DIALECT_STRICT` with packaged Common Tests v1.1, the supplied 50-algorithm benchmark produced 41 evaluated calibrations, seven `REFERENCE_NOT_EVALUATED` cases and two `BEHAVIOURAL_NOT_EVALUATED` cases. Algorithm 1, which had exposed the v4.26 oracle failure, calibrated at 100% after the v4.27 execution-contract correction.

### Reference-not-evaluated classification

Algorithms 9, 11, 12, 33, 35 and 36 have otherwise executable frozen reference Python whose first descriptive heading extends a historically truncated packaged `algorithm_title`. The packaged title is an exact long prefix of the frozen heading. Algorithm 25 is different: after its exact heading is treated as metadata, the frozen reference still contains a substantive malformed Python assignment and remains non-evaluable.

### Behavioural residual classification

- Algorithms 5 and 7 retain a source-specific unresolved punctuation sentinel in generated Python.
- Algorithm 17 differs from the frozen reference only in stdout spacing on the observed case.
- Algorithm 32 contains a frozen pseudocode loop-control discrepancy that changes selected answers; independently, `RAISE SystemExit` was being represented incorrectly in Python.
- Algorithm 39 exposed Python private name mangling of a protected AJ method name; after that representation issue is removed, a later `remove_cycle` behavioural difference remains visible.
- Algorithm 43 constructs strings containing brace placeholders as ordinary string data; changing those strings into implicit interpolation would alter the current AJ v1.4 string-data contract.
- Algorithm 44 passes two of three seeded cases; the remaining difference is an extra newline produced by the source's output structure.

These residuals are deliberately not normalised merely to increase the baseline score.

## v4.28 controlled diagnostic rerun

With the three v4.28 representation/execution corrections applied, the supplied corpus produced 48/50 evaluated calibrations in the local diagnostic environment. Algorithms 9, 11, 35 and 36 became evaluable and calibrated at 100%; Algorithms 12 and 33 became evaluable but exposed real placeholder-output differences; Algorithm 32 improved to 33.33% because the termination case became correct; Algorithm 39 progressed beyond the prior method-resolution crash and exposed its later behavioural difference. Algorithm 25 remained `REFERENCE_NOT_EVALUATED`.

Optional reference dependencies are environment-dependent, so the diagnostic status of dependency-sensitive algorithms is not a portable release invariant. The package invariant remains the fail-closed rule: missing dependencies yield non-evaluable evidence rather than fabricated expected behaviour.
