    cleaned_corpus <- CALL RemoveStopwordsAndPunctuation(corpus)
    tokenized_docs <- CALL TokenizeAndStem(cleaned_corpus)

    doc_term_matrix <- CALL CreateDocumentTermMatrix(tokenized_docs)
    lda_model <- CALL InitializeLDAModel(num_topics)

    CALL FitLDAModel(lda_model, doc_term_matrix)

    FOR EACH topic IN lda_model.get_topics() DO
        OUTPUT CALL ExtractTopWords(topic, top_n=10)
    ENDFOR
ENDFUNCTION