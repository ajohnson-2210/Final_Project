CLASS Stack
    stackArray <- CALL create_array(0, NONE)
    topIndex <- -1

    FUNCTION push ACCEPTS(item)
        topIndex <- topIndex + 1
        stackArray[topIndex] <- item

    ENDFUNCTION
    FUNCTION pop ACCEPTS()
        IF topIndex < 0 THEN
            RETURN NULL
            COMMENT Stack underflow
        ENDIF
        item <- stackArray[topIndex]
        topIndex <- topIndex - 1
        RETURN item

    ENDFUNCTION
    FUNCTION peek ACCEPTS()
        IF topIndex < 0 THEN
            RETURN NULL
        ENDIF
        RETURN stackArray[topIndex]
    ENDFUNCTION