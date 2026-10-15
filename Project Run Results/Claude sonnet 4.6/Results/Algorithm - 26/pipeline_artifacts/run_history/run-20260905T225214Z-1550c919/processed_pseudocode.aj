FUNCTION levelOrder ACCEPTS(root)
    IF root == NULL THEN
        RETURN EMPTY LIST
    ENDIF
    queue <- CALL list_value(root)
    result <- EMPTY LIST
    WHILE LENGTH OF queue > 0 DO
        level <- EMPTY LIST
        nextQueue <- EMPTY LIST
        FOR EACH node IN queue DO
            APPEND node.value TO level
            IF node.left != NULL THEN
                APPEND node.left TO nextQueue
            ENDIF
            IF node.right != NULL THEN
                APPEND node.right TO nextQueue
            ENDIF
        ENDFOR
        APPEND level TO result
        queue <- nextQueue
    ENDWHILE
    RETURN result
ENDFUNCTION