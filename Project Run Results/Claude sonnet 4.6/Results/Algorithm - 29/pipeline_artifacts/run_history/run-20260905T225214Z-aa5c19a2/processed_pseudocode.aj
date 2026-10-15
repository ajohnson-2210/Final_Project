FUNCTION classifyText ACCEPTS(text, categories, trainingData)
    preprocessed <- CALL tokenize(lowercase(CALL removeStopWords(text)))
    features <- CALL extractFeatures(preprocessed)
    COMMENT e.g. TF-IDF
    FOR EACH category IN categories DO
        score[category] <- CALL computeSimilarity(features, trainingData[category])
    ENDFOR
    RETURN category with highest score
ENDFUNCTION