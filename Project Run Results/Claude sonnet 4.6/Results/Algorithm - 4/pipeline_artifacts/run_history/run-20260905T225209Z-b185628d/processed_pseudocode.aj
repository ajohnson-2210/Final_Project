FUNCTION intersection ACCEPTS(A, B)
    result <- EMPTY LIST
    i <- 0
    j <- 0
    WHILE i < LENGTH OF A AND j < LENGTH OF B DO
        IF A[i] == B[j] THEN
            APPEND A[i] TO result
            i <- i + 1
            j <- j + 1
        ELSE IF A[i] < B[j] THEN
            i <- i + 1
        ELSE
            j <- j + 1
        ENDIF
    ENDWHILE
    RETURN result
ENDFUNCTION