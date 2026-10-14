password <- EMPTY STRING
num <- BOOLEAN(FALSE)
upper <- BOOLEAN(FALSE)
length <- BOOLEAN(FALSE)
passlist <- EMPTY LIST
loop <- BOOLEAN(TRUE)
WHILE loop == BOOLEAN(TRUE) DO
    password <- INPUT(STRING("Enter Password, it must be at least 8 Characters and contain at least 1 number and 1 uppercase letter : "))
    TRY
        passlist <- EMPTY LIST
        FOR EACH character IN password DO
            APPEND character TO passlist
        ENDFOR
        IF LENGTH OF passlist < 8 THEN
            RAISE CALL Exception()
        ELSE
            length <- BOOLEAN(TRUE)
        ENDIF
        FOR EACH x IN passlist DO
            IF x.isdigit() THEN
                num <- BOOLEAN(TRUE)
                BREAK
            ENDIF
        ENDFOR
        FOR EACH y IN passlist DO
            IF y.isupper() THEN
                upper <- BOOLEAN(TRUE)
                BREAK
            ENDIF
        ENDFOR
        IF ((length == BOOLEAN(TRUE))) AND ((num == BOOLEAN(TRUE))) AND ((upper == BOOLEAN(TRUE))) THEN
            OUTPUT STRING("Password Accepted!!")
        ELSE
            RAISE CALL Exception()
        ENDIF
        loop <- BOOLEAN(FALSE)
    CATCH
        OUTPUT STRING("That's Not a Valid Password, Please Try Again!")
        password <- EMPTY STRING
        num <- BOOLEAN(FALSE)
        upper <- BOOLEAN(FALSE)
        length <- BOOLEAN(FALSE)
    ENDTRY
ENDWHILE