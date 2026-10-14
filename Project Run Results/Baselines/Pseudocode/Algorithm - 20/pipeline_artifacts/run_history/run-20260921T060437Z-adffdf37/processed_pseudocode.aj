numvar <- 0
givenNum <- 0
numlist <- EMPTY LIST
loop <- BOOLEAN(TRUE)
WHILE loop == BOOLEAN(TRUE) DO
    givenNum <- INPUT(STRING("Enter Number: "))
    TRY
        givenNum <- CALL INTEGER(givenNum)
        loop <- BOOLEAN(FALSE)
    CATCH
        OUTPUT STRING("That's Not a Valid Number, Please Try Again!")
    ENDTRY
ENDWHILE
WHILE numvar <= givenNum DO
    numvar <- numvar + 1
    IF (givenNum MODULUS numvar) == 0 THEN
        APPEND numvar TO numlist
    ENDIF
ENDWHILE
WHILE loop == BOOLEAN(FALSE) DO
    TRY
        x <- numlist.pop(0)
        OUTPUT STRING("{x} is a Divisor of {givenNum}")
    CATCH
        QUIT
    ENDTRY
ENDWHILE