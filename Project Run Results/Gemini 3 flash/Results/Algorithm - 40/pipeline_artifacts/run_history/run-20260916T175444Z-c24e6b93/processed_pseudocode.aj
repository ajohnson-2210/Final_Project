CLASS QueueUsingStacks
    CONSTRUCTOR ACCEPTS()
        self.stack_in <- CALL create_stack()
        self.stack_out <- CALL create_stack()

    ENDCONSTRUCTOR
    METHOD Enqueue ACCEPTS(item)
        CALL PUSH(item, self.stack_in)

    ENDMETHOD
    METHOD Dequeue ACCEPTS()
        IF CALL stack_is_empty(self.stack_out) THEN
            WHILE NOT CALL stack_is_empty(self.stack_in) DO
                CALL PUSH(CALL POP(self.stack_in), self.stack_out)
            ENDWHILE
        ENDIF

        IF CALL stack_is_empty(self.stack_out) THEN
            RETURN STRING("Queue Empty")
        ENDIF
        RETURN CALL POP(self.stack_out)
    ENDMETHOD
ENDCLASS