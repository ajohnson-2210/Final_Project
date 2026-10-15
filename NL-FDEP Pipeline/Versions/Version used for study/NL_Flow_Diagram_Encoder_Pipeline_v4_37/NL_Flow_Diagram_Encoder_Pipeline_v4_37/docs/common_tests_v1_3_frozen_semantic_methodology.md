# Common Tests v1.3 — frozen task-semantic methodology

## Purpose

Common Tests v1.3 is the release-candidate evaluation pack for implementation-neutral behavioural measurement. The pack is prepared before official experimental scoring. It contains 50 algorithm suites and retains all 113 historical cases; 75 cases currently declare automated task-semantic expectations and 38 remain interaction/reference-only or human-review evidence.

## Academic-integrity boundary

For every automated semantic case, the input fixture and expected semantic outcome are explicit static data in the frozen test specification. During an experimental run NL-FDEP may only:

1. load the frozen fixture and static expected value;
2. invoke the submitted/generated program through the declared adapter;
3. observe the submitted program through the declared observer;
4. normalise that observed value according to the declared canonicalisation rule; and
5. compare the observation with the stored static expected value.

Experimental scoring must not execute a baseline program, reference implementation, or executable oracle to calculate an expected result from the experimental input. `runtime_expected_value_generation` is therefore false and a baseline reference is not required for experimental scoring.

## Semantic contracts

The original algorithm task defines the semantic interface: required task inputs and the result or state that constitutes correct behaviour. Parameter names, wrapper style, and incidental output prose are not part of the semantic contract unless the task requires them. Where an implementation exposes safely derivable arguments (for example matrix dimensions or conventional Tower-of-Hanoi peg labels), the mapping is declared in the frozen fixture rather than inferred from a model identity.

## Declarative invocation and observation

Task-specific execution knowledge lives in test metadata, not runtime `algorithm_id` branches. The frozen pack can declare function/class targets, permitted arity variants, typed structured fixtures, operation sequences, observation modes, canonical enumerations, sentinel equivalences, and numeric comparison tolerances. If a safe mapping is not declared, the case is `NOT_EVALUABLE`; the runtime does not invent semantics.

## Static expectations and provenance

Each enabled case uses `expectation_policy: STATIC_FROZEN_VALUE` and stores `expected_semantic_result` directly. The pack may retain descriptive provenance explaining how a fixture or expectation was established during test design, but that provenance is not executable and is not consulted to generate an expected answer during an experimental run.

## Baseline validation and experimental readiness gate

Baseline calibration is a separate validation activity used to demonstrate that the controlled benchmark remains consistent with the study environment. Under v4.35 RC3, a current trusted calibration is also a **procedural prerequisite** for beginning an `LLM_RESULTS_FOLDER` run: all 50 algorithms must be behaviourally evaluated and all 50 calibration scores must be 100%. A missing, stale, incomplete, or below-standard calibration blocks the experimental operation until the benchmark is corrected or recalibrated.

This gate does not make the baseline part of the experimental expected-value path. After readiness is established, the runner does not pass the baseline path into the experimental scorer. The scorer continues to use only the packaged static expectations and records that no runtime baseline reference was used.

## Human evaluation

The existing human-review questionnaire receives the same task-semantic contract for every algorithm. Human judgement therefore complements the automated result in tandem, including when automated execution is `NOT_EVALUABLE`; it does not replace or rewrite the automated status.

## Release-candidate use

v4.35 RC is intended for stress-testing across heterogeneous experimental datasets before the final study freeze. General evaluator defects may be corrected during this phase only when the correction can be specified independently of a particular model or result. After the final freeze, all official datasets must be rerun under the identical immutable instrument.
