FUNCTION convertGrade ACCEPTS(score)
    IF score >= 70 THEN
        RETURN STRING("Distinction")
    ELSE IF score >= 60 THEN
        RETURN STRING("Merit")
    ELSE IF score >= 50 THEN
        RETURN STRING("Pass")
    ELSE
        RETURN STRING("Fail")
    ENDIF
ENDFUNCTION