FUNCTION countVowels ACCEPTS(paragraph)
    counts <- EMPTY DICTIONARY
    counts[STRING("a")] <- 0
    counts[STRING("e")] <- 0
    counts[STRING("i")] <- 0
    counts[STRING("o")] <- 0
    counts[STRING("u")] <- 0
    FOR EACH __reserved_keyword__char IN CALL lowercase(paragraph) DO
        IF __reserved_keyword__char IN counts THEN
            counts[__reserved_keyword__char] <- counts[__reserved_keyword__char] + 1
        ENDIF
    ENDFOR
    RETURN counts
ENDFUNCTION