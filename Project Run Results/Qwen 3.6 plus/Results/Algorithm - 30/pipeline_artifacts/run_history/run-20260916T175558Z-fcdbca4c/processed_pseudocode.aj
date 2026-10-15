FUNCTION unnamed_function ACCEPTS(corpus)
    texts <- CALL preprocess(corpus)
    dtm <- CALL buildDocumentTermMatrix(texts)
    topics <- CALL applyLDA(dtm, numTopics)

    RETURN CALL extractTopWords(topics)
ENDFUNCTION