FUNCTION unnamed_function ACCEPTS(context, query)
    relevantPassages <- CALL retrievePassages(context, query)
    answer <- CALL extractAnswerSpan(relevantPassages, query)

    RETURN answer
ENDFUNCTION