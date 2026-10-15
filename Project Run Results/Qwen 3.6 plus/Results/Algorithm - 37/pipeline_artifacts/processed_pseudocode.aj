CLASS unnamed_class
    PROPERTY stack AS LIST
    PROPERTY size AS INTEGER

    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.stack <- EMPTY LIST
        PROPERTY THIS.size <- 0
    ENDCONSTRUCTOR

    METHOD push ACCEPTS(x)
        APPEND x TO THIS.stack
        THIS.size <- THIS.size + 1

    ENDMETHOD

    METHOD pop ACCEPTS()
        IF THIS.size > 0 THEN
            THIS.size <- THIS.size - 1
            RETURN THIS.stack.pop()
        ELSE
            RAISE STRING("ERROR")

        ENDIF
    ENDMETHOD

    METHOD peek ACCEPTS()
        IF THIS.size > 0 THEN
            RETURN THIS.stack[THIS.size-1]
        ELSE
            RAISE STRING("ERROR")
        ENDIF
    ENDMETHOD
ENDCLASS