# source_f Algorithm 30 — unbound CALL argument and abstract dependency audit — v3.13

## Source occurrence

```text
INPUT corpus

texts = preprocess(corpus)
dtm = buildDocumentTermMatrix(texts)
topics = applyLDA(dtm, numTopics)

RETURN extractTopWords(topics)
```

## Source-level findings

The response has two independent incompletenesses.

First, it names four essential NLP/topic-modelling operations without supplying definitions or imports:

```text
preprocess(...)
buildDocumentTermMatrix(...)
applyLDA(...)
extractTopWords(...)
```

Their implementations cannot be reconstructed without inventing algorithmic semantics. They remain abstract/undefined routine dependencies.

Second, `numTopics` is passed as a value argument to `applyLDA` but is neither an input nor assigned earlier in the routine. There is no representation evidence from which a value can be recovered, so the pipeline must not synthesise a parameter or assignment.

## v3.13 semantic result

Generic compatibility processing still faithfully produces:

```text
FUNCTION unnamed_function ACCEPTS(corpus)
    texts <- CALL preprocess(corpus)
    dtm <- CALL buildDocumentTermMatrix(texts)
    topics <- CALL applyLDA(dtm, numTopics)
    RETURN CALL extractTopWords(topics)
ENDFUNCTION
```

v3.13 now rejects this during `STATIC_SEMANTIC_ANALYSIS` with:

```text
Identifier 'numTopics' is read before declaration or assignment at line 4.
```

The routine names themselves are not rejected merely for being undefined, preserving the existing undefined-routine boundary.

## Classification

**EXPECTED FAIL — ABSTRACT / UNDEFINED ROUTINE DEPENDENCIES + UNBOUND SOURCE IDENTIFIER**

The pipeline does not implement LDA, invent `numTopics`, add a parameter, or otherwise repair the source algorithm.
