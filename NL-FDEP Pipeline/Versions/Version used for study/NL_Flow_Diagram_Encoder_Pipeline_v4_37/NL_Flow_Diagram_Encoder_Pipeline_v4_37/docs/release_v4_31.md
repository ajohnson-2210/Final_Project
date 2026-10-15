# NL-FDEP v4.31 release note

Pipeline: **NL-FDEP v4.31**  
Dialect: **AJ_24038155 Dialect v1.5**  
Scoring rubric: **v1.1 (unchanged)**  
Scoring schema: **v1.4 (unchanged)**  
Common Test Design: **v1.1 (unchanged; 50 suites / 113 tests)**

## Purpose

v4.31 introduces the approved AJ_24038155 Dialect v1.5 language change for explicit source-authored import directives and the standard-library punctuation adapter used by the frozen baseline corpus.

The change is intentionally language-level and versioned. It is not an Algorithm 5/7 special case and does not convert arbitrary comments into executable code.

## AJ v1.5 import directives

The Strict parser recognises only these exact COMMENT payload families:

```text
COMMENT import <module>
COMMENT import <module> AS <alias>
COMMENT from <module> import <name>
COMMENT from <module> import <name1>, <name2>, ...
COMMENT from <module> import *
```

Recognised directives emit a dedicated `ImportDirectiveNode`, are preserved in the flow model as `IMPORT`, and lower deterministically to the corresponding Python import statement.

All other `COMMENT` lines remain ordinary non-executable comments.

## AJ v1.5 punctuation adapter

The exact source identifier:

```text
string_method_punctuation
```

now has the declared lowering:

```text
string.punctuation
```

The source remains responsible for the module declaration, e.g.:

```text
COMMENT import string
```

No general punctuation predicate or undefined spelling is inferred.

## Baseline impact

Algorithms 5 and 7 already contain both source-authored constructs required by v1.5:

```text
COMMENT import string
```

and:

```text
char NOT IN string_method_punctuation
```

Under v1.5 these constructs have explicit dialect semantics and can be tested against their trusted references without inventing missing behaviour.

## Provenance and compatibility

- Baseline Benchmark Folder processing remains fixed to `AJ_DIALECT_STRICT`.
- All AJ v1.4 programs remain valid under v1.5.
- Generic Compatibility does not gain permission to invent imports or punctuation predicates.
- Common Tests v1.1 are unchanged.
- Scoring Rubric v1.1 and Scoring Schema v1.4 are unchanged.
- A pipeline-version change forces normal provenance/currentness invalidation for existing artefacts.

## Validation

Release validation completed with:

- pytest: **1,256 passed, 3 skipped, 5 subtests passed**;
- unittest: **383 passed, 1 skipped**;
- Strict parse/flow/compile audit: **50/50 baseline pseudocode algorithms**;
- focused baseline calibration for Algorithms 5 and 7: **100% / 100%** against their packaged Common Tests and trusted references; and
- reconstructed corrected 50-algorithm baseline calibration: **50/50 calibrated**, **43 SUCCESS / 7 measured behavioural FAILURE**, mean baseline calibration **88.0%**.

The reconstructed baseline uses the previously confirmed Algorithm 2 and Algorithm 25 reference corrections and the corrected Algorithm 50 pseudocode used for the v4.30 study run. The user's own baseline folder should still be rerun under v4.31 to freeze the official study artefacts.
