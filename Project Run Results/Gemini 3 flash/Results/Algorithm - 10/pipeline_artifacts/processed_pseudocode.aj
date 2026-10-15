FUNCTION CountVowels ACCEPTS(text)
    vowel_counts <- EMPTY DICTIONARY
    vowel_counts[STRING("a")] <- 0
    vowel_counts[STRING("e")] <- 0
    vowel_counts[STRING("i")] <- 0
    vowel_counts[STRING("o")] <- 0
    vowel_counts[STRING("u")] <- 0

    FOR EACH __reserved_keyword__char IN CALL lowercase(text) DO
        IF __reserved_keyword__char IN vowel_counts THEN
            vowel_counts[__reserved_keyword__char] <- vowel_counts[__reserved_keyword__char] + 1
        ENDIF
    ENDFOR

    RETURN vowel_counts
ENDFUNCTION