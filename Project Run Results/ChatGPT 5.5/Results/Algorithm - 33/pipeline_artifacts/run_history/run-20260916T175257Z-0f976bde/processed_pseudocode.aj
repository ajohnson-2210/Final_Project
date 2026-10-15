FUNCTION unnamed_function ACCEPTS(Number)
        Low <- 0
        High <- Number
        Answer <- 0

        WHILE Low <= High DO
            Mid <- (Low + High) INTEGER DIVISION 2

            IF Mid * Mid == Number THEN
                OUTPUT Mid
                RETURN
            ELSE IF Mid * Mid < Number THEN
                Answer <- Mid
                Low <- Mid + 1
            ELSE
                High <- Mid - 1
            ENDIF
        ENDWHILE

        OUTPUT Answer
ENDFUNCTION