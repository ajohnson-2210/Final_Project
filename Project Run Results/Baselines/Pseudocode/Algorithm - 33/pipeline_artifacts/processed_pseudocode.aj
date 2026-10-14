FUNCTION int_sqrt ACCEPTS(n)
    IF n < 2 THEN
        RETURN n
    ENDIF
    left <- 1
    right <- n INTEGER DIVISION 2
    ans <- 1
    WHILE left <= right DO
        mid <- (left + right) INTEGER DIVISION 2
        sq <- mid * mid
        IF sq == n THEN
            RETURN mid
        ELSE IF (sq < n) THEN
            ans <- mid
            left <- mid + 1
        ELSE
            right <- mid - 1
        ENDIF
    ENDWHILE
    RETURN ans
ENDFUNCTION

__reserved_keyword__integer <- 0
loop <- BOOLEAN(TRUE)
WHILE loop == BOOLEAN(TRUE) DO
    TRY
        __reserved_keyword__integer <- INPUT(STRING("Enter a Positive Integer to find the Square Root: "))
        __reserved_keyword__integer <- CALL INTEGER(__reserved_keyword__integer)
        IF __reserved_keyword__integer <= 0 THEN
            __reserved_keyword__integer <- 0
            RAISE CALL ValueError()
        ELSE
            loop <- BOOLEAN(FALSE)
        ENDIF
    CATCH
        OUTPUT STRING("That's Not a Valid Number, Please Try Again!")
    ENDTRY
ENDWHILE
message <- STRING("The Square Root of ") + CALL STRING(__reserved_keyword__integer) + STRING(" Rounded Down to the Nearest Integer = ")
square_root <- CALL int_sqrt(__reserved_keyword__integer)
OUTPUT STRING("{message} {square_root}")