FUNCTION trainTopicModel ACCEPTS(corpus)
    COMMENT Preprocess all documents (tokenization, remove stopwords, stemming)
    COMMENT Create a bag-of-words representation (document-term matrix)
    COMMENT Apply an algorithm like Latent Dirichlet Allocation (LDA)
    COMMENT Extract top words for each topic
    topicModel <- trainedLDA
    RETURN topicModel

ENDFUNCTION
FUNCTION getTopics ACCEPTS(topicModel, numberOfTopics)
    topics <- EMPTY LIST
    FOR EACH topic IN topicModel DO
        topWords <- get top words for this topic
        APPEND topWords TO topics
    ENDFOR
    RETURN topics
ENDFUNCTION