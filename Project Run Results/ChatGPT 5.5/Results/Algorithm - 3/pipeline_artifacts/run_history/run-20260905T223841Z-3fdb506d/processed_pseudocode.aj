FUNCTION unnamed_function ACCEPTS(Year)
        IF (Year MODULUS 400 == 0) THEN
            OUTPUT STRING("Leap Year")
        ELSE IF (Year MODULUS 100 == 0) THEN
            OUTPUT STRING("Not Leap Year")
        ELSE IF (Year MODULUS 4 == 0) THEN
            OUTPUT STRING("Leap Year")
        ELSE
            OUTPUT STRING("Not Leap Year")
        ENDIF
ENDFUNCTION