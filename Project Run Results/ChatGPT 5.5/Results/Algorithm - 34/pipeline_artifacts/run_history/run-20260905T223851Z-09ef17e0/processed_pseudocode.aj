FUNCTION unnamed_function ACCEPTS(List1, List2)
        Result <- EMPTY SET

        FOR EACH Item IN List1 DO
            IF Item IN List2 THEN
                CALL add_to_set(Result, Item)
            ENDIF
        ENDFOR

        OUTPUT Result
ENDFUNCTION