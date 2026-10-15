FUNCTION countVowels ACCEPTS(paragraph)
    vowelCount <- EMPTY DICTIONARY
    vowelCount[STRING("a")] <- 0
    vowelCount[STRING("e")] <- 0
    vowelCount[STRING("i")] <- 0
    vowelCount[STRING("o")] <- 0
    vowelCount[STRING("u")] <- 0
    FOR EACH __reserved_keyword__char IN paragraph DO
        lowerChar <- CALL lowercase(__reserved_keyword__char)
        IF lowerChar IN vowelCount THEN
            vowelCount[lowerChar] <- vowelCount[lowerChar] + 1
        ENDIF
    ENDFOR
    RETURN vowelCount
ENDFUNCTION