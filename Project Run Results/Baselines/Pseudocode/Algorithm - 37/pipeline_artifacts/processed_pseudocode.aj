CLASS Stack
    PROPERTY items
    PROPERTY top
    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.items <- EMPTY LIST
        PROPERTY THIS.top <- -1
    ENDCONSTRUCTOR
    METHOD show ACCEPTS()
        stack_items <- THIS.items
        OUTPUT STRING("Stack:  {stack_items}")
    ENDMETHOD
    METHOD push ACCEPTS(value)
        new_length <- LENGTH OF THIS.items + 1
        temp <- EMPTY LIST
        FOR fill_index <- IN RANGE 0 TO new_length DO
            APPEND NONE TO temp
        ENDFOR
                i <- 0
        FOR EACH x IN THIS.items DO
            temp[i] <- x
            i <- i + 1
        ENDFOR
        temp[THIS.top + 1] <- value
        PROPERTY THIS.items <- temp
        PROPERTY THIS.top <- THIS.top + 1
        OUTPUT STRING("Pushed:  {value}")
        THIS.show()
    ENDMETHOD
    METHOD pop ACCEPTS()
        IF THIS.is_empty() THEN
            OUTPUT STRING("Pop attempted on empty stack")
            THIS.show()
            RETURN NONE
        ENDIF
        value <- THIS.items[THIS.top]
        new_length <- LENGTH OF THIS.items - 1
        temp <- EMPTY LIST
        FOR fill_index <- IN RANGE 0 TO new_length DO
            APPEND NONE TO temp
        ENDFOR
                i <- 0
        WHILE i < new_length DO
            temp[i] <- THIS.items[i]
            i <- i + 1
        ENDWHILE
        PROPERTY THIS.items <- temp
        PROPERTY THIS.top <- THIS.top - 1
        OUTPUT STRING("Popped:  {value}")
        THIS.show()
        RETURN value
    ENDMETHOD
    METHOD peek ACCEPTS()
        IF THIS.is_empty() THEN
            OUTPUT STRING("Peek attempted on empty stack")
            THIS.show()
            RETURN NONE
        ENDIF
        value <- THIS.items[THIS.top]
        OUTPUT STRING("Peeked:  {value}")
        THIS.show()
        RETURN value
    ENDMETHOD
    METHOD is_empty ACCEPTS()
        RETURN THIS.top == -1
    ENDMETHOD
    METHOD size ACCEPTS()
        RETURN THIS.top + 1
    ENDMETHOD
ENDCLASS

s <- CALL Stack()
s.push(10)
s.push(20)
s.push(30)
s.peek()
s.pop()
s.peek()
s.pop()
s.pop()
s.pop()
s.peek()