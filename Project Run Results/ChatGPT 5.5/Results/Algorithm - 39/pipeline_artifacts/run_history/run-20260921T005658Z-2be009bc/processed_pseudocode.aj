FUNCTION unnamed_function ACCEPTS(Head)
    Slow <- Head
    Fast <- Head

    WHILE Fast != NULL AND Fast.Next != NULL DO
        Slow <- Slow.Next
        Fast <- Fast.Next.Next

        IF Slow == Fast THEN
            OUTPUT STRING("Cycle Detected")
            RETURN
        ENDIF
    ENDWHILE

    OUTPUT STRING("No Cycle")
ENDFUNCTION