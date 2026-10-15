FUNCTION unnamed_function ACCEPTS(root)
    IF root == null THEN
        RETURN EMPTY LIST

    ENDIF
    queue <- CALL list_value(root)
    result <- EMPTY LIST

    WHILE LENGTH OF queue > 0 DO
        levelSize <- LENGTH OF queue
        currentLevel <- EMPTY LIST

        FOR _ <- IN RANGE 0 TO (levelSize-1) + 1 DO
            node <- queue.pop(0)
            APPEND node.value TO currentLevel

            IF node.left THEN
                APPEND node.left TO queue

            ENDIF
            IF node.right THEN
                APPEND node.right TO queue

            ENDIF
        ENDFOR
        APPEND currentLevel TO result

    ENDWHILE
    RETURN result
ENDFUNCTION