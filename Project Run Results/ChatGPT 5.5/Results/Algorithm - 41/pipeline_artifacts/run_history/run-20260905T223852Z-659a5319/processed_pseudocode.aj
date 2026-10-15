    INPUT N

    CREATE N * N board

    FUNCTION Solve(Row)
        IF Row == N THEN
            OUTPUT Board
            RETURN
        ENDIF

        FOR Col <- 0 TO N-1
            IF Position(Row, Col) is safe THEN
                PLACE Queen at (Row, Col)

                Solve(Row + 1)

                REMOVE Queen from (Row, Col)
            ENDIF
        ENDFOR
    END FUNCTION

    Solve(0)
END