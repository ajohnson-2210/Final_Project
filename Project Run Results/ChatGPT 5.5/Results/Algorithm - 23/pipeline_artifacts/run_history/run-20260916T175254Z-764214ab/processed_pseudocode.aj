FUNCTION unnamed_function ACCEPTS(Score)
        IF Score >= 70 THEN
            OUTPUT STRING("Distinction")
        ELSE IF Score >= 50 THEN
            OUTPUT STRING("Merit")
        ELSE IF Score >= 40 THEN
            OUTPUT STRING("Pass")
        ELSE
            OUTPUT STRING("Fail")
        ENDIF
ENDFUNCTION