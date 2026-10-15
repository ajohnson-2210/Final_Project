    INPUT Year

    IF (Year MOD 400 = 0) THEN
        OUTPUT "Leap Year"
    ELSE IF (Year MOD 100 = 0) THEN
        OUTPUT "Not Leap Year"
    ELSE IF (Year MOD 4 = 0) THEN
        OUTPUT "Leap Year"
    ELSE
        OUTPUT "Not Leap Year"
    ENDIF
END