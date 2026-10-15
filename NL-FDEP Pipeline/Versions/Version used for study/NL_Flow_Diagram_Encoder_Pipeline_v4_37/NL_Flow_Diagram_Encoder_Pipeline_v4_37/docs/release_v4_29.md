# NL-FDEP v4.29 — optional external-module lowering for Algorithm 50

Pipeline: **NL-FDEP v4.29**  
AJ Dialect: **1.4**  
Scoring Rubric: **1.1**  
Scoring Schema: **1.4**  
Common Test Design: **1.1** (50 suites / 113 executable tests)

## Scope

v4.29 is a narrow compiler correction for explicit external-library adapter calls already present in canonical Strict AJ pseudocode. It does not change Common Test semantics, scoring, the AJ language standard, or baseline/reference files.

The compiler now lowers the frozen adapter spellings used by Algorithm 50 (`numpy_method_*`, `matplotlib_method_*`, and `matplotlib_animation_method_FuncAnimation`) to NumPy/Matplotlib calls and injects imports only when those adapters are present.

The externally supplied Algorithm 50 benchmark pseudocode also contains three source/reference transcription differences that are not silently repaired by the compiler: the call to `generate_obstacles` must pass the reference default `20`, and the two coloured marker `scatter` calls must place size before colour for the positional Matplotlib signature. A corrected source file is supplied separately to the user; NL-FDEP does not rewrite the benchmark automatically.

## Optional dependencies

Algorithm 50 requires `numpy` and `matplotlib` in the same Python interpreter running NL-FDEP. If unavailable, the test remains `BEHAVIOURAL_NOT_EVALUATED`; missing packages are not treated as expected algorithm behaviour.

## Behavioural contract

With the corrected Algorithm 50 pseudocode, NumPy/Matplotlib available, `MPLBACKEND=Agg`, and seed 104729, both trusted reference and generated Python complete the existing Common Test with return code 0 and empty stdout.
