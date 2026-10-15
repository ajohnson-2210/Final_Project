    INPUT Head

    Slow <- Head
    Fast <- Head

    WHILE Fast ≠ NULL AND Fast.Next ≠ NULL
        Slow <- Slow.Next
        Fast <- Fast.Next.Next

        IF Slow = Fast THEN
            OUTPUT "Cycle Detected"
            STOP
        ENDIF
    ENDWHILE

    OUTPUT "No Cycle"
END