FUNCTION unnamed_function ACCEPTS(s)
    chars <- CALL to_array(s)
    left <- 0
    right <- LENGTH OF s-1

    WHILE left < right DO
        temp_var <- chars[left]
        chars[left] <- chars[right]
        chars[right] <- temp_var
        left <- left + 1
        right <- right - 1

    ENDWHILE
    RETURN JOIN(chars, EMPTY STRING)
ENDFUNCTION