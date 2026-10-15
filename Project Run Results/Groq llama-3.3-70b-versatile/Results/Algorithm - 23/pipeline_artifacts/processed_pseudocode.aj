FUNCTION CONVERT_SCORE ACCEPTS(score)
  IF score >= 90 THEN
    RETURN STRING("Distinction")
  ELSE IF score >= 70 AND score < 90 THEN
    RETURN STRING("Merit")
  ELSE IF score >= 50 AND score < 70 THEN
    RETURN STRING("Pass")
  ELSE
    RETURN STRING("Fail")
  ENDIF
ENDFUNCTION