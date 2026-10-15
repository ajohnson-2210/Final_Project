FUNCTION extractTopics ACCEPTS(corpus, numTopics)
    tokens <- tokenize and clean each document in corpus
    vocabulary <- CALL buildVocabulary(tokens)
    termMatrix <- CALL buildDocumentTermMatrix(tokens, vocabulary)
    topics <- CALL initializeRandomTopicAssignments(numTopics)
    REPEAT until convergence
        FOR each document
            FOR each word
                UPDATE topic assignment using probability distribution
                UPDATE topic-word and document-topic counts
    RETURN top N words per topic as topic descriptions
ENDFUNCTION