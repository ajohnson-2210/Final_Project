# Common Tests v1.3 — Frozen Task-Semantic Evaluation

Common Tests v1.3 is a pre-experiment frozen evaluation pack. It retains 50 suites and 113 cases. Automated semantic cases contain explicit input fixtures and explicit static expected semantic values. Experimental evaluation may execute only the submitted/generated program, normalise the observed result using the declarative observer stored with the test, and compare that result with the static expected value.

The evaluator must not execute a baseline program, reference implementation, or executable oracle to derive an expected result from an experimental input. Task-specific observation rules are declarative test metadata; runtime evaluator code is algorithm-agnostic. Human review uses the same frozen semantic contract.
