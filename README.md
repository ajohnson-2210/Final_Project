# NL-FDEP

**Natural Language to Flow Diagram Execution Pipeline**

**MSc Computer Science Final Project**

> A comparative evaluation framework for examining how transformer based language models convert natural language algorithm specifications into structured pseudocode, formal intermediate representations, executable Python and behaviourally testable software.

Repository:  
https://github.com/ajohnson-2210/Final_Project

---

## Project Overview

NL-FDEP is a multi-stage software pipeline developed to investigate the reliability of transformer-based language models when generating structured algorithmic representations from natural-language specifications.

Rather than evaluating only the final source code produced by a model, NL-FDEP retains and analyses the intermediate representations through which an algorithm is transformed.

The principal processing pathway is:

```text
Natural-Language Algorithm Specification
                ↓
     Transformer Language Model
                ↓
          Pseudocode
                ↓
   Pseudocode Canonicalisation
                ↓
      Abstract Syntax Tree
                ↓
 Machine-Readable Flow Diagram
                ↓
             Python
                ↓
      Behavioural Testing
                ↓
   Automated / Human Analysis
```

The project was designed around a central principle:

> **Semantic alignment must be preserved and not invented.**

NL-FDEP may normalise recognised differences in representation, but it must not repair missing algorithmic logic or invent behaviour that was not present in the language-model output.

---

## Research Objective

The research evaluates whether transformer based language models can reliably transform natural language algorithm specification into structured pseudocode that can subsequently be processed into executable representations without losing the original algorithmic intent.

The study examines:

- whether generated pseudocode can be processed deterministically;
- whether algorithmic structure is preserved through AST and flow representations;
- whether the resulting executable Python demonstrates the required behaviour;
- how model performance differs across algorithms;
- how automated assessment compares with independent Human Review; and
- where semantic or representational failures first become observable.

The wider research title is:

> **A Comparative Evaluation Of Transformer Based Language Models For the generation of Structured Algorithmic Representations such as Pseudocode and Executable Flow Diagrams from Natural Language Algorithm Specifications.**

---

## Why NL-FDEP Uses Intermediate Representations

Many language model code generation evaluations compare a natural language prompt directly with generated source code.

NL-FDEP instead exposes the transformation pathway.

```text
Pseudocode
    ↓
Processed Pseudocode
    ↓
AST
    ↓
Flow Representation
    ↓
Python
    ↓
Test Results
```

Each stage produces an artefact that can be retained and inspected.

This makes it possible to investigate not only **whether an implementation failed**, but also **where the first meaningful divergence became visible**.

For example, a failure can potentially be traced to:

- the model generated pseudocode;
- pseudocode interpretation;
- parsing;
- AST construction;
- AST to flow conversion;
- flow validation;
- Python generation; or
- behavioural execution.

The intermediate representations therefore provide analytical evidence rather than functioning only as temporary compiler structures.

---

## Strict Pseudocode Dialect

Pseudocode has no universally accepted syntax.

Equivalent operations can be represented using different keywords, punctuation, indentation styles and natural language expressions. This flexibility is useful for human communication but becomes problematic when pseudocode is used as direct input to a deterministic parser.

NL-FDEP therefore uses a strict pseudocode dialect adapted from the pseudocode conventions used for Cambridge International AS & A Level Computer Science.

The purpose is to:

- reduce unnecessary representational variation;
- provide a predictable machine processable interface;
- retain human readability;
- permit deterministic parsing; and
- keep responsibility for the actual algorithmic reasoning with the language model.

The dialect does **not** require every model to produce the same algorithm.

It constrains how common operations are represented while still permitting alternative valid algorithmic solutions.

---

## Canonicalisation

Model generated pseudocode is interpreted and canonicalised according to a defined processing profile before parsing.

Canonicalisation may resolve recognised representational variation where the intended construct is already present.

It must not:

- invent conditions;
- introduce missing loops;
- repair incorrect algorithmic logic;
- create operations absent from the original output; or
- transform an incorrect algorithm into a correct one.

The original pseudocode and canonicalised pseudocode are retained separately to support traceability.

The governing principle is:

> **Representational form may be normalised, but algorithmic meaning must not be invented.**

---

## Abstract Syntax Tree

Accepted canonical pseudocode is converted into an Abstract Syntax Tree.

The AST makes the structure of the generated algorithm explicit and separates algorithmic constructs from the surface formatting of the pseudocode.

Examples of represented constructs include:

- assignments;
- conditions;
- loops;
- inputs;
- outputs;
- function or procedure calls;
- returns;
- expressions; and
- nested structures.

Both machine readable and visual representations may be retained.

The AST also provides an inspection point between textual pseudocode and the later flow representation.

---

## Machine Readable Flow Representation

The AST is transformed into a machine readable graph representing algorithmic control flow.

This stage makes relationships such as:

- sequencing;
- decisions;
- branches;
- loops;
- termination; and
- execution paths

explicit.

The underlying graph is the authoritative computational representation.

Visual diagrams are generated from this representation for inspection and explanation, but graphical layout does not determine program semantics.

---

## Flow Diagram to Python

A significant architectural decision in the NL-FDEP is that Python is generated from the **flow representation**, not directly from the original pseudocode.

```text
Pseudocode → AST → Flow Representation → Python
```

This prevents the pipeline from producing a flow diagram merely for presentation and then bypassing it during execution.

The executable program therefore depends on the intermediate transformations.

If semantic structure is lost during AST or flow conversion, the effects can potentially become visible in the generated Python and subsequent behavioural tests.

---

## Alternative Flow-Diagram Input

The NL-FDEP also supports a structured flow diagram as an alternative input route.

```text
Structured Flow Diagram
        ↓
Machine-Readable Graph
        ↓
       Python
        ↓
Behavioural Testing
```

This pathway is separate from the principal six model experiment.

It demonstrates that the architecture is concerned with controlled representations of algorithmic intent rather than pseudocode alone.

A Tic-Tac-Toe validation example was used to demonstrate this pathway using a structured Draw.io representation containing:

- 35 shapes;
- 50 connectors;
- a Player 1 winning demonstration; and
- a complete nine-move draw demonstration.

Both demonstration scenarios passed.

---

# Experimental Study

## Models Evaluated

Six transformer based language model datasets were evaluated:

| Model |
---------
| ChatGPT 5.5 |
| Claude sonnet 4.6 |
| Deepseek |
| Gemini 3 flash |
| Groq llama-3.3-70b-versatile |
| Qwen 3.6 plus |

Each model received the same **50 natural language algorithm specifications**.

This produced:

```text
6 models × 50 algorithms = 300 model algorithm observations
```

The dataset consistency checks confirmed that all six datasets contained the expected 50 algorithm identifiers.

---

## Frozen Experimental Version

The comparative study was conducted using:

> **NL-FDEP v4.37**

The experimental pipeline, test framework and scoring procedures were frozen before the comparative results were finalised.

Later development changes are not retrospectively applied to the experimental results.

This separation is necessary to ensure that all six model datasets remain evaluated under the same experimental conditions.

---

## Trusted Baseline

Before the language model outputs were evaluated, a trusted baseline containing corresponding algorithm examples was processed through the NL-FDEP.

The baseline is a **study-readiness control**, not a runtime correctness oracle.

Its purpose is to answer:

> **Can NL-FDEP successfully process a trusted implementation of this problem?**

Experimental behavioural testing asks the separate question:

> **Does the model generated implementation demonstrate the behaviour required by the specification?**

The trusted baseline achieved successful processing across the complete 50 algorithm set before experimental evaluation.

One text-processing baseline example incorporates an adapted passage from Kenneth Grahame's *The Wind in the Willows* (1908), Chapter I, *The River Bank*.

---

## Common Tests

Behavioural correctness is evaluated using a frozen Common Tests framework.

The study test package contains:

- **50 algorithm suites**
- **156 declared test cases**

comprising:

| Test Category | Count |
-------------------------
| Core Behavioural | 129 |
| Pre-Freeze Validation | 8 |
| Semantic Boundary Probes | 19 |
| **Total** | **156** |

Core Behavioural tests form the primary behavioural evaluation surface.

Semantic Boundary Probes are reported separately because behaviour outside the primary contract is not automatically equivalent to correctness or incorrectness.

Passing the supplied test suite provides empirical evidence for the tested behaviour. It does not constitute formal proof of universal program correctness.

---

## Independent Human Review

Automated assessment is complemented by independent Human Review.

Human Review examines retained generated artefacts and predefined criteria rather than replacing behavioural execution.

Across the completed study:

```text
300 algorithm reviews
6 datasets
50 algorithms per dataset
800 Human Review criteria evaluations per model dataset
```

Human Review serves several purposes:

- provides an independent assessment stream;
- identifies disagreement with automated assessment;
- allows intermediate representations to be inspected together;
- exposes infrastructure limitations; and
- prevents automated structural measures from being treated as unquestionable semantic truth.

Disagreement between automated and Human Review evidence is retained as an analytical result rather than hidden.

---

## Human Review Failure-to-Demonstrate Rule

A completed Human Review may occasionally reach a terminal state in which numerical rubric performance cannot legitimately be demonstrated.

The NL-FDEP distinguishes this from missing or incomplete data.

Only the explicit terminal state:

```text
HUMAN_REVIEW_COMPLETE_NOT_EVALUABLE
```

receives zero credit under the fixed-denominator Human Review procedure.

Missing, incomplete or technically unresolved reviews are **not** automatically converted to zero.

This is referred to as the:

> **Fixed-denominator failure-to-demonstrate rule**

rather than missing-value imputation.

---

# Study Results

Across the complete 300 observation study:

- **225 observations were evaluable**
- **75 observations were Not Evaluable**
- **179 evaluable observations reached the reference behavioural level**
- **46 evaluable observations were below the reference level**

The principal model-level results were:

| Model | Mean Behavioural | Common Test Accuracy | Pipeline Success |
----------------------------------------------------------------------
| Claude sonnet 4.6 | 88.97% | 87.10% | 39/50 |
| ChatGPT 5.5 | 84.86% | 84.52% | 35/50 |
| Deepseek | 83.75% | 82.65% | 42/50 |
| Groq llama-3.3-70b-versatile | 79.64% | 75.28% | 46/50 |
| Gemini 3 flash | 77.94% | 81.48% | 39/50 |
| Qwen 3.6 plus | 74.67% | 73.47% | 42/50 |

A particularly important result is that **pipeline success did not equate to behavioural correctness**.

This demonstrates why structural processability and semantic correctness are retained as separate evidence streams.

---

## Final Combined Results

The final study aggregation combines the automated overall result with the completed Human Review Overall using equal weighting.

| Rank | Model | Final Combined Score |
---------------------------------------
| 1 | Claude sonnet 4.6 | **92.56%** |
| 2 | Deepseek | **89.86%** |
| 3 | ChatGPT 5.5 | **89.84%** |
| 4 | Gemini 3 flash | **86.53%** |
| 5 | Qwen 3.6 plus | **84.95%** |
| 6 | Groq llama-3.3-70b-versatile | **84.19%** |

These scores are study defined comparative summaries.

They should not be interpreted as permanent or universal rankings of the underlying commercial language model products.

Model performance depends on:

- model version;
- task selection;
- prompting;
- experimental configuration;
- evaluation criteria; and
- changes made by hosted model providers over time.

---

# NL-FDEP v4.38

## Post Study Maintenance Update

The NL-FDEP **v4.38** was developed after completion of the frozen v4.37 experimental study.

The update addresses infrastructure issues identified through independent Human Review of the retained v4.37 artefacts.

The changes concern automated structural assessment and **do not alter the original model generated outputs**.

Two principal issues were identified.

---

## Nested-Structure Reachability

In some algorithms involving more complex structures, including nested loops and class or method related constructs, the v4.37 automated structural analysis could report AST or flow nodes as unreachable.

Human inspection of the corresponding artefacts showed that some of these reported reachability failures occurred despite valid control flow relationships being present.

This could create an automated disagreement where semantic structure had in fact been preserved.

v4.38 improves the relevant validation logic so that legitimate nested and method related structures are handled more accurately.

---

## AST to Flow Node Differences

The second issue concerned comparisons between AST node counts and flow node counts.

An AST and a flow graph are different intermediate representations.

A one to one node relationship is therefore not always expected.

Some AST nodes are structural or representational and may be legitimately absorbed or omitted when converted into executable flow structure.

Under v4.37, some valid AST to flow differences could nevertheless be interpreted automatically as missing structure.

Human Review demonstrated cases where the apparent difference did **not** correspond to semantic loss.

v4.38 therefore improves this comparison so that legitimate representational differences are not automatically classified as failures.

---

## Why This Matters

The update reinforces a fundamental NL-FDEP principle:

> **Semantic preservation does not require structural identity.**

The AST primarily represents hierarchical program structure.

The flow graph primarily represents execution relationships.

The representations can therefore differ structurally while still describing the same algorithmic behaviour.

The purpose of validation is to identify loss of semantically relevant structure, not to require identical node counts between fundamentally different representations.

---

## v4.37 Versus v4.38

| Version | Role |
------------------
| **v4.37** | Frozen version used for the six-model comparative experiment |
| **v4.38** | Post-study maintenance version incorporating issues discovered through Human Review process|

The experimental study has **not been recalculated using v4.38**.

This is intentional.

Once the experimental environment had been frozen, later software changes were prevented from modifying the historical experimental record.

Applying v4.38 retrospectively would mean that some study observations had been processed under different infrastructure from that originally used for the experiment.

The v4.37 results are therefore retained as the authoritative experimental results.

v4.38 represents continued software validation and improvement.

---

## Human Review as Pipeline Validation

The discovery of the v4.37 issues also demonstrates the value of retaining independent Human Review.

```text
Automated Assessment
        ↓
Independent Human Review
        ↓
Disagreement Identified
        ↓
Intermediate Artefacts Inspected
        ↓
Infrastructure Issue Confirmed
        ↓
Post-Study Correction
        ↓
NL-FDEP v4.38
```

The corrections do not repair experimental model outputs.

They correct the infrastructure used to interpret relationships between generated intermediate representations.

This distinction is central to maintaining the integrity of the study.

---

# Validation

The NL-FDEP underwent regression and study readiness validation before and during preparation of the experimental release.

Recorded validation evidence includes:

- **1,377 pytest tests passed**
- **3 pytest tests skipped**
- **5 separately recorded subtests**
- **481 unittest tests passed**
- **1 unittest test skipped**
- **1,087 checksum files verified**
- **50/50 trusted baseline algorithms successfully processed**

A principal path numerical demonstration also validated the end to end sequence using the summation example:

```text
0  → 0
1  → 1
5  → 15
10 → 55
```

Result:

```text
4 / 4 tests passed
```

The alternative flow input Tic-Tac-Toe demonstration produced:

```text
2 / 2 demonstration tests passed
```

These demonstrations provide validation evidence for the processing infrastructure. They are not substitutes for the frozen experimental Common Tests.

---

# Evidence Streams

NL-FDEP deliberately avoids reducing every observation into one opaque definition of “quality”.

The analytical framework retains separate evidence concerning:

- pipeline progression;
- representation outcomes;
- Core Behavioural performance;
- Common Test accuracy;
- Semantic Boundary Variance;
- automated rubric assessment;
- independent Human Review;
- reference comparison; and
- final study level comparative summaries.

This allows cases such as the following to remain visible:

```text
Structurally Processable ≠ Behaviourally Correct
```

and:

```text
Automated Structural Disagreement ≠ Proven Semantic Failure
```

---

# Controlled Intermediate Representation

The strict pseudocode dialect used in NL-FDEP raises a wider research question concerning controlled intermediate representations.

A possible generalised concept is a **Controlled Intermediate Language (CIL)**:

> A deliberately restricted intermediate representation intended to provide a consistent, human readable and machine processable interface between natural language algorithm specifications and formal structural representations.

NL-FDEP does **not** claim that its current pseudocode dialect constitutes a universal CIL.

The concept is instead proposed as a future research direction.

Potential future comparisons include:

```text
Natural Language
      ↓
Strict Pseudocode
      ↓
Formal Structure
```

and:

```text
Human-Produced Structured Flow
              ↓
      Machine-Readable Graph
              ↓
            Code
```

The broader research question is therefore not necessarily whether pseudocode itself should be universally standardised.

It may instead concern:

> **the standardisation of the interface between human algorithmic intent and machine readable structure.**

---

# Reproducibility

The NL-FDEP was designed to retain an audit trail from model output to analytical result.

Relevant artefacts may include:

- original generated pseudocode;
- processed pseudocode;
- canonicalisation reports;
- parser output;
- AST representations;
- AST visualisations;
- flow graph data;
- flow visualisations;
- Draw.io representations;
- generated Python;
- compilation information;
- Common Test results;
- scoring artefacts;
- Human Review records; and
- analytical dashboard data.

For reproduction of the dissertation experiment, the relevant **v4.37 frozen study configuration and artefacts** should be used.

For subsequent development or new experimental work, **v4.38 or a later validated release** should normally be preferred.

Results generated under later versions should not be silently substituted for the original v4.37 study results.

---

# Software Requirements

A formal Software Requirements Specification was produced for NL-FDEP.

The specification defines:

- functional requirements;
- non functional requirements;
- pipeline stage requirements;
- data retention requirements;
- evaluation requirements;
- Human Review requirements;
- study constraints;
- validation criteria;
- acceptance evidence;
- traceability requirements; and
- version/change-control requirements.

The requirements document should be read alongside the implementation when reviewing how the research methodology is represented in software.

---

# Research Artefacts and Dashboards

The project includes analytical outputs used to inspect the completed study.

These include:

- comparative heat map analysis;
- 50 algorithm radial profiles;
- comparative radial model views;
- Human Review analysis; and
- final scoring analysis.

Dashboards are **downstream analytical and presentation tools**.

They do not execute the experiment and do not retrospectively determine whether an algorithm is correct.

The underlying retained study artefacts remain the authoritative evidence.

---

# Ethical and Responsible Use

The principal research objects are generated software artefacts rather than personal or sensitive human data.

Human Review concerns generated artefacts and predefined assessment criteria.

The study does not attempt to profile individual users.

Because hosted language models can change over time, results are reported in relation to:

- the collected datasets;
- recorded model identifiers;
- the frozen pipeline version;
- the defined experimental conditions.

The reported results should therefore not be interpreted as permanent product rankings.

---

## Experimental Models

The six listed transformer based language models were experimental subjects whose outputs formed the comparative dataset.


---

# Selected Source Attribution

The strict pseudocode conventions were adapted from the pseudocode guidance published for Cambridge International AS & A Level Computer Science.

# Relevant citations include:

Full academic references are provided in the associated research report.

---

# Important Interpretation Notes

The NL-FDEP is an experimental research framework.

The following distinctions are important:

> **Passing a test is evidence of tested behaviour, not formal proof of universal correctness.**

> **Pipeline success is not equivalent to semantic correctness.**

> **A trusted baseline establishes infrastructure readiness; it is not the runtime oracle for model generated algorithms.**

> **An AST provides structural evidence; it does not independently prove behavioural equivalence.**

> **A visual flow diagram is a representation of the underlying graph; graphical layout is not program semantics.**

> **Human Review complements automated analysis rather than automatically overriding it.**

> **v4.38 improves the post-study infrastructure but does not rewrite the frozen v4.37 experimental record.**

---

# Repository

This repository provides the public project location for the NL-FDEP and its associated MSc research artefacts.

**Repository:**  
https://github.com/ajohnson-2210/Final_Project

When using the project for academic or reproducibility purposes, record the specific NL-FDEP version used.

---

# Citation

If referencing the software repository in academic work, a suitable citation is:

> Johnson, A. (2026) *Final_Project: NL-FDEP – Natural Language–Flow Diagram Execution Pipeline* [GitHub repository]. GitHub. Available at: https://github.com/ajohnson-2210/Final_Project

The accompanying MSc research report should also be cited where the experimental methodology, study results or interpretation are used.

---

# Project Status

**Experimental study:** Complete  
**Frozen study version:** NL-FDEP v4.37  
**Current post-study maintenance version:** NL-FDEP v4.38  
**Experimental datasets:** 6  
**Algorithms per dataset:** 50  
**Total model-algorithm observations:** 300

---

## Author

**Alan Johnson**  
MSc Computer Science Final Project  
2026
