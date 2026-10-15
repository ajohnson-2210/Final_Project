FUNCTION unnamed_function ACCEPTS(s)
    maxLen <- 0
    start <- 0
    seen <- EMPTY DICTIONARY

    FOR i <- IN RANGE 0 TO (LENGTH OF s-1) + 1 DO
        IF s[i] in seen AND seen[s[i]] >= start THEN
            start <- seen[s[i]] + 1

        ENDIF
        seen[s[i]] <- i
        maxLen <- CALL max(maxLen, i - start + 1)

    ENDFOR
    RETURN maxLen
ENDFUNCTION