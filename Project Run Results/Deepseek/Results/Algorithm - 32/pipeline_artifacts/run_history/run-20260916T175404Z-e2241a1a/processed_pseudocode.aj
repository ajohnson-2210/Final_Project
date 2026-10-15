FUNCTION answerQuestion ACCEPTS(question, context)
    COMMENT Preprocess question and context
    COMMENT Use an information retrieval or a QA model (e.g., BERT-based)
    COMMENT Identify the most relevant span in the context that answers the question
    answer <- extractedSpan
    RETURN answer
ENDFUNCTION