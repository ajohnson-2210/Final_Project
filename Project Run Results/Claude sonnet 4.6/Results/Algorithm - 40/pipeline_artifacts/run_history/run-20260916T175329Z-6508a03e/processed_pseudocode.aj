CLASS Queue
    PROPERTY stack1 AS LIST
    PROPERTY stack2 AS LIST

    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.stack1 <- EMPTY LIST
        PROPERTY THIS.stack2 <- EMPTY LIST
    ENDCONSTRUCTOR

    METHOD enqueue ACCEPTS(item)
        APPEND item TO THIS.stack1
    ENDMETHOD

    METHOD dequeue ACCEPTS()
        IF LENGTH OF THIS.stack2 == 0 THEN
            WHILE LENGTH OF THIS.stack1 > 0 DO
                APPEND CALL POP(THIS.stack1) TO THIS.stack2
            ENDWHILE
        ENDIF
        IF LENGTH OF THIS.stack2 == 0 THEN
            RETURN STRING("Underflow")
        ENDIF
        RETURN CALL POP(THIS.stack2)
    ENDMETHOD
ENDCLASS