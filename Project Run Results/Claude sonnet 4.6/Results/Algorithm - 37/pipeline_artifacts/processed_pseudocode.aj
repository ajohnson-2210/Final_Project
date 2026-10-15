CLASS Stack
    PROPERTY data AS LIST

    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.data <- EMPTY LIST
    ENDCONSTRUCTOR

    METHOD push ACCEPTS(item)
        APPEND item TO THIS.data

    ENDMETHOD

    METHOD pop ACCEPTS()
        IF LENGTH OF THIS.data == 0 THEN
            RETURN STRING("Underflow")
        ENDIF
        RETURN REMOVE LAST ITEM FROM THIS.data

    ENDMETHOD

    METHOD peek ACCEPTS()
        IF LENGTH OF THIS.data == 0 THEN
            RETURN STRING("Empty")
        ENDIF
        RETURN THIS.data[-1]
    ENDMETHOD
ENDCLASS