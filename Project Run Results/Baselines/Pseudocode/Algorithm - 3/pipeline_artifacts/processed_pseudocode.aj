leap <- BOOLEAN(FALSE)
year <- 0
loop <- BOOLEAN(TRUE)
WHILE loop == BOOLEAN(TRUE) DO
    year <- INPUT(STRING("Enter Year: "))
    TRY
        year <- CALL INTEGER(year)
        loop <- BOOLEAN(FALSE)
    CATCH
        OUTPUT STRING("That's Not a Valid Year, Please Try Again!")
    ENDTRY
ENDWHILE
IF (year MODULUS 4) == 0 THEN
    leap <- BOOLEAN(TRUE)
ELSE
    leap <- BOOLEAN(FALSE)
ENDIF
IF (((year MODULUS 100) == 0)) AND (NOT (((year MODULUS 400) == 0))) THEN
    leap <- BOOLEAN(FALSE)
ELSE IF ((year MODULUS 400) == 0) THEN
    leap <- BOOLEAN(TRUE)
ENDIF
IF NOT (leap) THEN
    OUTPUT STRING("{year} is Not a Leap Year!")
ELSE
    OUTPUT STRING("{year} Is a Leap Year!")
ENDIF