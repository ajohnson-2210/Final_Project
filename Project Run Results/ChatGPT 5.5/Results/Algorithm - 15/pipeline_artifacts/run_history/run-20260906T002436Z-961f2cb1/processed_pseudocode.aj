FUNCTION unnamed_function ACCEPTS(Array)
        Largest <- CALL negative_infinity()
        SecondLargest <- CALL negative_infinity()

        FOR EACH Number IN Array DO
            IF Number > Largest THEN
                SecondLargest <- Largest
                Largest <- Number
            ELSE IF Number > SecondLargest AND Number < Largest THEN
                SecondLargest <- Number
            ENDIF
        ENDFOR

        OUTPUT SecondLargest
ENDFUNCTION