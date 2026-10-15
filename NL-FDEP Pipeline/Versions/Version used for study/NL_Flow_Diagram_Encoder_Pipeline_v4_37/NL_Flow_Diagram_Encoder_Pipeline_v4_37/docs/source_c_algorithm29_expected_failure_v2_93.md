# source_c Algorithm 29 expected-failure audit — v2.93

## Motivating study occurrence

```text
FUNCTION trainTextClassifier(documents, labels):
    // Step 1: Preprocess each document (tokenization, stopword removal, stemming)
    // Step 2: Create a vocabulary from the training set
    // Step 3: Convert each document to a feature vector (e.g., TF-IDF)
    // Step 4: Train a classifier (e.g., Naive Bayes, SVM, or Neural Network) on the feature vectors
    model = trainedModel
    RETURN model

FUNCTION predictCategory(model, newText):
    // Preprocess the new text similarly
    // Convert to feature vector
    // Use model to predict the category
    RETURN predictedCategory
```

The comments describe the missing algorithmic work, but they do not bind `trainedModel` or `predictedCategory` and they do not define/import executable preprocessing, feature extraction, training or prediction operations.

## v2.92 behaviour

The compatibility layer preserved the abstract comments and direct placeholders, then strict parsing/static semantics accepted the program. Generated Python consequently contained unbound value names such as `trainedModel` and `predictedCategory`; this was a false executable pass.

## v2.93 correction

The parser's static semantic validator now enforces the unambiguous direct subset of AJ's declared/assigned-before-read rule. A bare identifier used directly as:

- an assignment RHS;
- a property-assignment RHS;
- a `RETURN` value; or
- an `OUTPUT` value

must already be bound by the visible scope (for example a parameter, prior assignment or enclosing binding).

This is a corpus-wide AST semantic rule. It contains no source_c/model/file/algorithm/function-name condition.

The legacy compatibility sentinel `NULL` remains explicitly recognised so this change does not alter the existing non-canonical NULL compatibility path. Canonical AJ v1.1 continues to use `NONE`.

## Deliberate scope boundary

v2.93 does **not** introduce full compound-expression or control-flow definite-assignment analysis. For example, detecting an unbound identifier nested inside `a + missing` is a broader semantic change and remains a separate audit candidate. This prevents the approved source_c 29 correction from silently expanding into unrelated historical compatibility changes.

## Classification

```text
Algorithm: source_c 29 — Text Classification Model
status: EXPECTED FAIL — ABSTRACT ALGORITHM / UNBOUND RESULT DEPENDENCIES
failure stage: STATIC_SEMANTIC_ANALYSIS
unbound direct values: trainedModel, predictedCategory
semantic inference required for complete execution: YES
algorithmic reconstruction required: YES
pipeline must invent classifier implementation: NO
dialect change: NO
```

AJ_24038155 Dialect v1.1 remains frozen and unchanged.
