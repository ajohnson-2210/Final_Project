# Common Tests v1.4 — semantic-boundary methodology

## Purpose

Common Tests v1.4 extends the frozen task-semantic evaluation pack with a second, explicitly separate observation stream for **Semantic Boundary Variance (SBV)**.

The semantic contract derived from the original task specification remains authoritative. The boundary stream asks a different question from core correctness: **does the generated implementation accept and process inputs that the task contract places outside its intended semantic domain?**

## Score streams

Every case is assigned one of two streams.

### `CORE_BEHAVIOURAL`

Core cases use a frozen input fixture and a static pre-experiment expected semantic value. They contribute to:

- per-algorithm task-semantic Common Test accuracy;
- experimental semantic behavioural percentage;
- dataset-level aggregate Common Test accuracy;
- existing P2/P3/P4 behavioural evidence where applicable.

### `SEMANTIC_BOUNDARY_PROBE`

Boundary probes use a frozen out-of-domain fixture but **do not carry an expected semantic output**. They never enter the core behavioural denominator.

Each evaluable probe is classified as:

- `OUT_OF_DOMAIN_ACCEPTED` — the task entry point completed successfully;
- `CONTROLLED_REJECTION` — the probe raised an explicitly configured validation error type;
- `INCIDENTAL_FAILURE` — execution failed, but not through a configured controlled-rejection mechanism;
- `NOT_EVALUABLE` — no safe/unambiguous semantic invocation was possible.

The descriptive measure is:

```text
Semantic Boundary Variance (%)
    = OUT_OF_DOMAIN_ACCEPTED / evaluable boundary probes × 100
```

A high SBV indicates that an implementation extends beyond the frozen semantic input domain. It is **not automatically a penalty** and is not interpreted as core behavioural incorrectness.

## Baseline role

The baseline may execute the same frozen v1.4 semantic cases during calibration so that candidate fixtures and boundary behaviour can be inspected before the final study freeze. This validation activity does not change the contract and does not create runtime expected values for experimental scoring.

Experimental scoring remains oracle-free:

- baseline Python is not supplied to an LLM run;
- no reference implementation is executed to derive an expected experimental result;
- all core expected values are static before the experimental run;
- boundary probes are observational and classify only the submitted/generated implementation's response.

## v1.4 audit corrections

The v1.3 semantic-boundary audit resulted in the following immediate corrections:

- **Algorithm 20 — divisors:** zero and negative integers are outside `POSITIVE_INTEGER` and are moved from ordinary boundary cases to the SBV stream.
- **Algorithm 22 — factorial:** the contract is resolved as `NON_NEGATIVE_INTEGER`; `0! = 1` is a required core boundary case. Negative integers are outside-domain probes.
- **Algorithm 33 — integer square root:** zero is valid under `NON_NEGATIVE_INTEGER` and is now a core boundary case; negative input is a boundary probe.
- **Algorithm 40 — queue using two stacks:** evidence metadata now correctly records that the frozen operation sequence reaches an empty dequeue and expects `EMPTY`.
- Legacy wording claiming semantic fixtures were “not externally injectable” has been removed from v1.4.

## Boundary-capable suites in RC8

Automatically runnable semantic-boundary probes are included for algorithms 2, 4, 12, 20, 22, 23, 27, 28, 33, 36, 43, 44, 45 and 46. Algorithms 35 and 41 declare a boundary probe but keep it `NOT_EVALUABLE` until safe generic adapters exist for their human-supported interfaces.

Other algorithms continue to use core behavioural expansion or descriptive-only boundary evidence where the task specification does not define a sufficiently defensible out-of-domain boundary.
