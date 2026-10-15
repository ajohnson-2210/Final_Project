FUNCTION levelOrderTraversal ACCEPTS(root)
    IF root == NULL THEN
        RETURN EMPTY LIST
    ENDIF
    result <- EMPTY LIST
    queue <- CALL create_queue()
    CALL ENQUEUE(queue, root)
    WHILE NOT CALL queue_is_empty(queue) DO
        levelSize <- CALL queue_size(queue)
        currentLevel <- EMPTY LIST
        FOR i <- IN RANGE 0 TO (levelSize-1) + 1 DO
            node <- CALL DEQUEUE(queue)
            APPEND node.value TO currentLevel
            IF node.left != NULL THEN
                CALL ENQUEUE(queue, node.left)
            ENDIF
            IF node.right != NULL THEN
                CALL ENQUEUE(queue, node.right)
            ENDIF
        ENDFOR
        APPEND currentLevel TO result
    ENDWHILE
    RETURN result
ENDFUNCTION