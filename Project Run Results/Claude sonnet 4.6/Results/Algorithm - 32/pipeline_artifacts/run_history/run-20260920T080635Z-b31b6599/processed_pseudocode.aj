FUNCTION answerQuestion ACCEPTS(question, context)
    qTokens <- CALL tokenize(question)
    cTokens <- CALL tokenize(context)
    qEmbedding <- CALL embed(qTokens)
    FOR EACH sentence IN context DO
        score[sentence] <- CALL similarity(qEmbedding, CALL embed(sentence))
    ENDFOR
    bestSentence <- sentence with highest score
    answer <- CALL extractAnswerSpan(question, bestSentence)
    RETURN answer
ENDFUNCTION