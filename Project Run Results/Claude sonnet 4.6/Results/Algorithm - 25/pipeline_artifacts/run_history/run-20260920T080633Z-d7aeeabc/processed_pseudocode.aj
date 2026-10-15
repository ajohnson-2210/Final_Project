FUNCTION longestUniqueSubstring ACCEPTS(str)
    seen <- EMPTY DICTIONARY
    maxLen <- 0
    start <- 0
    FOR i <- IN RANGE 0 TO (LENGTH OF str - 1) + 1 DO
        IF str[i] IN seen AND seen[str[i]] >= start THEN
            start <- seen[str[i]] + 1
        ENDIF
        seen[str[i]] <- i
        maxLen <- CALL max(maxLen, i - start + 1)
    ENDFOR
    RETURN maxLen
ENDFUNCTION