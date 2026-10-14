OUTPUT STRING("First Non Repeating Character In a String")

FUNCTION fnon_repeat ACCEPTS(s)
    chars <- EMPTY LIST
    FOR EACH character IN s DO
        APPEND character TO chars
    ENDFOR
    counts <- EMPTY LIST
    FOR fill_index <- IN RANGE 0 TO LENGTH OF chars DO
        APPEND 0 TO counts
    ENDFOR
        i <- 0
    WHILE i < LENGTH OF chars DO
        j <- 0
        WHILE j < LENGTH OF chars DO
            IF chars[i] == chars[j] THEN
                counts[i] <- counts[i] + 1
            ENDIF
            j <- j + 1
        ENDWHILE
        i <- i + 1
    ENDWHILE
    i <- 0
    WHILE i < LENGTH OF chars DO
        IF counts[i] == 1 THEN
            RETURN ((STRING("String = ") + s) + STRING(" Result: ")) + chars[i]
        ENDIF
        i <- i + 1
    ENDWHILE
    RETURN ((STRING("String = ") + s) + STRING(" Result: ")) + CALL STRING(NONE)
ENDFUNCTION

OUTPUT CALL fnon_repeat(STRING("swiss"))
OUTPUT CALL fnon_repeat(STRING("aabbccd"))
OUTPUT CALL fnon_repeat(STRING("aabbcc"))