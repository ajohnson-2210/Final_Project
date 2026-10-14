FUNCTION common ACCEPTS(a, b)
    result <- EMPTY LIST
    i <- 0
    WHILE i < LENGTH OF a DO
        item <- a[i]
        j <- 0
        found_in_b <- BOOLEAN(FALSE)
        WHILE j < LENGTH OF b DO
            IF b[j] == item THEN
                found_in_b <- BOOLEAN(TRUE)
                BREAK
            ENDIF
            j <- j + 1
        ENDWHILE
        IF found_in_b THEN
            k <- 0
            already_in_result <- BOOLEAN(FALSE)
            WHILE k < LENGTH OF result DO
                IF result[k] == item THEN
                    already_in_result <- BOOLEAN(TRUE)
                    BREAK
                ENDIF
                k <- k + 1
            ENDWHILE
            IF NOT (already_in_result) THEN
                APPEND item TO result
            ENDIF
        ENDIF
        i <- i + 1
    ENDWHILE
    RETURN result
ENDFUNCTION

firstlist <- LIST [5, 8, 6, 3, 6, 9, 7, 0, 2]
secondlist <- LIST [2, 4, 3, 1, 7, 9, 7, 3]
common_elements <- CALL common(firstlist, secondlist)
OUTPUT STRING("{firstlist}\n{secondlist} \nCommon Elements: {common_elements}")