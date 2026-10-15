FUNCTION unnamed_function ACCEPTS(Array, Target)
        Low <- 0
        High <- LENGTH OF Array - 1

        WHILE Low <= High DO
            Mid <- (Low + High) INTEGER DIVISION 2

            IF Array[Mid] == Target THEN
                OUTPUT Mid
                RETURN
            ENDIF

            IF Array[Low] <= Array[Mid] THEN
                IF Target >= Array[Low] AND Target < Array[Mid] THEN
                    High <- Mid - 1
                ELSE
                    Low <- Mid + 1
                ENDIF
            ELSE
                IF Target > Array[Mid] AND Target <= Array[High] THEN
                    Low <- Mid + 1
                ELSE
                    High <- Mid - 1
                ENDIF
            ENDIF
        ENDWHILE

        OUTPUT STRING("Not Found")
ENDFUNCTION