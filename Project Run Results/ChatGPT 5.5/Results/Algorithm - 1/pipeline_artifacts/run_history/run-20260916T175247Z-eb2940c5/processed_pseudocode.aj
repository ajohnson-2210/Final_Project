FUNCTION unnamed_function ACCEPTS(String1, String2)
        IF LENGTH OF String1 != LENGTH OF String2 THEN
            OUTPUT STRING("Not Anagrams")
        ELSE
            String1 <- CALL sort_characters(String1)
            String2 <- CALL sort_characters(String2)

            IF String1 == String2 THEN
                OUTPUT STRING("Anagrams")
            ELSE
                OUTPUT STRING("Not Anagrams")
            ENDIF
        ENDIF
ENDFUNCTION