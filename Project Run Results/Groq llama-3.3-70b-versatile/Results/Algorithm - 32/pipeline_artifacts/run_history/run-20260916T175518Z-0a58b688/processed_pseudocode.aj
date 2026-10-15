FUNCTION QUESTION_ANSWERING ACCEPTS(text, query)
  COMMENT Use a question answering algorithm to find the answer
  answer <- CALL FIND_ANSWER(text, query)
  RETURN answer
ENDFUNCTION