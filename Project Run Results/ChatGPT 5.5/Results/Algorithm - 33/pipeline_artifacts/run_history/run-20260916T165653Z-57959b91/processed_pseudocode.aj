    INPUT Number

    Low <- 0
    High <- Number
    Answer <- 0

    WHILE Low ≤ High
        Mid <- (Low + High) DIV 2

        IF Mid × Mid = Number THEN
            OUTPUT Mid
            STOP
        ELSE IF Mid × Mid < Number THEN
            Answer <- Mid
            Low <- Mid + 1
        ELSE
            High <- Mid - 1
        ENDIF
    ENDWHILE

    OUTPUT Answer
END