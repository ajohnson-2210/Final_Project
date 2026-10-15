FUNCTION longestSubstringLength ACCEPTS(str)
    n <- LENGTH OF str
    seen <- EMPTY SET
    maxLen <- 0
    left <- 0
    FOR right <- IN RANGE 0 TO (n-1) + 1 DO
        WHILE str[right] IN seen DO
            seen.remove(str[left])
            left <- left + 1
        ENDWHILE
        CALL add_to_set(seen, str[right])
        maxLen <- CALL max(maxLen, right - left + 1)
    ENDFOR
    RETURN maxLen
ENDFUNCTION