CLASS QueueUsingStacks
    COMMENT (for enqueue)
    COMMENT (for dequeue)
    PROPERTY stack1
    PROPERTY stack2

    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.stack1 <- CALL create_stack()
        PROPERTY THIS.stack2 <- CALL create_stack()
    ENDCONSTRUCTOR

    METHOD enqueue ACCEPTS(item)
        CALL PUSH(item, THIS.stack1)
    ENDMETHOD

    METHOD dequeue ACCEPTS()
        IF CALL stack_is_empty(THIS.stack2) THEN
            WHILE NOT CALL stack_is_empty(THIS.stack1) DO
                CALL PUSH(CALL POP(THIS.stack1), THIS.stack2)
            ENDWHILE
        ENDIF
        IF CALL stack_is_empty(THIS.stack2) THEN
            RETURN NULL
            COMMENT LENGTH OF Queue == 0
        ENDIF
        RETURN CALL POP(THIS.stack2)
    ENDMETHOD
ENDCLASS