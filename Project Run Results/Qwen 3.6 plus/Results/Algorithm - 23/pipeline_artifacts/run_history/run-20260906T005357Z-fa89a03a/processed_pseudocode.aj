FUNCTION unnamed_function ACCEPTS(score)
    IF score >= 80 THEN
        RETURN STRING("Distinction")
    ELSE IF score >= 60 THEN
        RETURN STRING("Merit")
    ELSE IF score >= 40 THEN
        RETURN STRING("Pass")
    ELSE
        RETURN STRING("Fail")
    ENDIF
ENDFUNCTION