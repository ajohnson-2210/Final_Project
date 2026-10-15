# source_b Algorithms 30–36 audit — v2.80

## Scope and evidence role

This record continues the version-controlled audit of the source_b study responses. The exact study occurrences are retained in `tests/test_source_b_algorithms30_36_audit_v2_80.py` so each determination remains reproducible without folding the six complete raw study files into the distributable project tree.

The audit distinguishes three outcomes:

1. **expected abstract failure** — executable behaviour is not sufficiently specified, so no recovery measure is justified;
2. **unchanged pass** — the existing v2.79 pipeline already handles the supplied algorithm and no new measure is introduced; and
3. **pass after approved general recovery** — the occurrence exposes a general, semantic-preserving pipeline defect and motivates a regression-protected measure.

## Algorithm 30 — Topic Modelling System

### Source characteristics

The response contains high-level stages such as:

    tokens <- tokenize and clean each document in corpus
    REPEAT until convergence
    UPDATE topic assignment using probability distribution
    UPDATE topic-word and document-topic counts
    RETURN top N words per topic as topic descriptions

The response does not define tokenisation/cleaning behaviour, convergence criteria, the probability distribution, the update equations, or the procedure for selecting the reported top words.

### Classification

    status:
        EXPECTED FAIL — ABSTRACT / NON-EXECUTABLE ALGORITHM DESCRIPTION

    structural recovery sufficient:
        NO

    semantic inference required for execution:
        YES

    algorithmic reconstruction required:
        YES

    pipeline change justified:
        NO

The remaining abstract statements are intentionally retained in the processed source and strict parsing fails. No normalisation measure is introduced.

## Algorithm 31 — Co-reference Resolution

### Source characteristics

The response explicitly names conceptual NLP stages:

    extractNamedEntities(text)
    extractMentions(text)
    findNearestEntities(pronoun, entities)
    scoreAndRank(candidates, pronoun)
    MAP pronoun TO bestMatch
    RETURN coreferenceMap

The behaviour of the extraction, candidate generation and ranking stages is undefined. `MAP pronoun TO bestMatch` is also an abstract mapping operation, and the returned `coreferenceMap` is not concretely initialised or constructed.

### Classification

    status:
        EXPECTED FAIL — ABSTRACT / NON-EXECUTABLE ALGORITHM DESCRIPTION

    structural recovery sufficient:
        NO

    semantic inference required for execution:
        YES

    algorithmic reconstruction required:
        YES

    pipeline change justified:
        NO

No executable mapping machinery is invented.

## Algorithm 32 — Question Answering System

### Source characteristics

The response describes a QA pipeline using:

    tokenize(...)
    embed(...)
    similarity(...)
    sentence with highest score
    extractAnswerSpan(...)

These are processing stages rather than defined algorithms. `score[sentence]` is used without an explicit score collection initialisation, and `sentence with highest score` is an abstract selection instruction rather than executable AJ.

### Classification

    status:
        EXPECTED FAIL — ABSTRACT / NON-EXECUTABLE ALGORITHM DESCRIPTION

    structural recovery sufficient:
        NO

    semantic inference required for execution:
        YES

    algorithmic reconstruction required:
        YES

    pipeline change justified:
        NO

As with Algorithm 29, the pipeline is not credited for inventing executable NLP behaviour from a conceptual description.

## Algorithm 33 — Integer Square Root

The response is concrete executable pseudocode. Existing v2.79 measures already recover the comma-compressed initial assignments, inline branches, loop form and integer division. It parses and compiles without any new v2.80 rule.

    status:
        PASS — EXISTING PIPELINE

    new pipeline change justified:
        NO

## Algorithm 34 — Union/Common Elements Without Duplicates

The supplied algorithm explicitly converts the first list to a set, iterates the second list, checks membership and duplicate suppression, and appends matching items. Existing v2.79 normalisation already handles the conventional `convert list1 to set` form and list construction.

    status:
        PASS — EXISTING PIPELINE

    new pipeline change justified:
        NO

## Algorithm 35 — LRU Cache

### Source characteristics

The response describes an LRU cache using an ordered dictionary and conceptual recency operations:

    MOVE key to most recently used position
    REMOVE least recently used (front) item
    INSERT key:value at most recently used position

The response does not define the executable representation or mechanics required to implement those recency updates. Converting these phrases into list/dictionary operations would require choosing implementation details not supplied by the response.

### Classification

    status:
        EXPECTED FAIL — ABSTRACT DATA-STRUCTURE OPERATIONS

    structural recovery sufficient:
        NO

    semantic inference required for execution:
        YES

    algorithmic reconstruction required:
        YES

    pipeline change justified:
        NO

No LRU implementation is invented.

## Algorithm 36 — Binary Search in Rotated Sorted Array

### Empirical defect

The source is concrete and complete, but it uses conventional mathematical chained comparisons:

    arr[low] <= target < arr[mid]
    arr[mid] < target <= arr[high]

AJ v1.0 permits one comparison operator per comparison expression. Before v2.80, the Pratt parser nevertheless accepted an unparenthesised chain and left-associated it. Therefore:

    arr[low] <= target < arr[mid]

was compiled as the equivalent of:

    (arr[low] <= target) < arr[mid]

rather than the intended:

    arr[low] <= target AND target < arr[mid]

This was a semantic-integrity false pass: parsing succeeded while generated Python changed the condition's meaning.

### Approved general measure — GC195

v2.80 adds a conservative control-condition normalisation for unparenthesised comparison chains whose operands are side-effect-free value expressions.

For example:

    a < b <= c < d

becomes:

    a < b AND b <= c AND c < d

source_b Algorithm 36 therefore becomes:

    IF arr[low] <= target AND target < arr[mid] THEN
    IF arr[mid] < target AND target <= arr[high] THEN

Every operand and comparison is explicit in the source. The rule does not invent a new condition; it expresses the conventional chain using existing canonical AJ Boolean syntax.

### Side-effect safeguard

GC195 does not duplicate potentially effectful operands. Chains containing `CALL`, `INPUT`, `RANDOM`, or other unsupported function-style operations are left unexpanded.

The strict AJ parser is also tightened to enforce the frozen grammar boundary: if an unparenthesised comparison chain reaches strict parsing, it is rejected with an explicit chained-comparison error rather than silently left-associated. Explicitly parenthesised comparison results remain distinguishable and are not treated as an implicit chain.

### Classification

    status:
        PASS AFTER STRUCTURAL / SEMANTIC-PRESERVING COMPARISON-CHAIN RECOVERY

    source problem:
        conventional mathematical chained comparison syntax lies outside
        canonical AJ v1.0 comparison-expression form

    v2.79 behaviour:
        false pass; chain was parsed as left-associated binary comparisons

    required recovery:
        expand safe chains into conjunctions of adjacent comparisons

    semantic inference:
        NONE

    algorithmic reconstruction:
        NO

    control flow changed:
        NO

    source condition changed:
        NO — the same explicit relations are represented in AJ form

    new grammar feature:
        NO

    general rule:
        YES — GC195 safe comparison-chain recovery

    strict semantic-integrity safeguard:
        reject any unexpanded unparenthesised chain

## Regression evidence

v2.80 includes regressions for:

- exact source_b Algorithms 30–36 study occurrences;
- expected-failure retention for Algorithms 30, 31, 32 and 35;
- unchanged passing behaviour for Algorithms 33 and 34;
- exact Algorithm 36 chain recovery and behavioural correctness across the rotated-array example;
- arbitrary three-comparison safe chains;
- already-canonical `AND` comparisons remaining unchanged;
- side-effecting chains not being expanded or silently compiled;
- strict rejection of unparenthesised chained comparisons; and
- preservation of explicitly parenthesised comparison-result expressions.


## Post-v4.01 definite-assignment amendment

The original v2.80 record correctly described Algorithm 33 as a pass under the then-current direct textual binding check. A later semantic-integrity audit activated conservative control-flow definite assignment for that same AJ rule. `result` is assigned only inside one branch of a potentially zero-iteration loop and is then read by `RETURN result`; the validator does not infer numeric invariants that would guarantee the assignment. Algorithm 33 is therefore now classified as an expected static-semantic failure unless the source explicitly initialises `result` before the loop. No initialisation is invented by normalisation.
