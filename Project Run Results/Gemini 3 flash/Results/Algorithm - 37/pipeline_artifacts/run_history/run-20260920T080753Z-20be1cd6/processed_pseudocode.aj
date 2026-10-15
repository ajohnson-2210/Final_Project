CLASS Stack
    CONSTRUCTOR ACCEPTS(capacity)
        self.arr <- CALL create_array(capacity, NONE)
        self.top_index <- -1

    ENDCONSTRUCTOR
    METHOD Push ACCEPTS(item)
        IF self.top_index == LENGTH OF self.arr - 1 THEN
            RETURN STRING("Overflow Error")
        ENDIF
        self.top_index <- self.top_index + 1
        self.arr[self.top_index] <- item

    ENDMETHOD
    METHOD Pop ACCEPTS()
        IF self.top_index == -1 THEN
            RETURN STRING("Underflow Error")
        ENDIF
        item <- self.arr[self.top_index]
        self.top_index <- self.top_index - 1
        RETURN item

    ENDMETHOD
    METHOD Peek ACCEPTS()
        IF self.top_index == -1 THEN
            RETURN STRING("Stack Empty")
        ENDIF
        RETURN self.arr[self.top_index]
    ENDMETHOD
ENDCLASS