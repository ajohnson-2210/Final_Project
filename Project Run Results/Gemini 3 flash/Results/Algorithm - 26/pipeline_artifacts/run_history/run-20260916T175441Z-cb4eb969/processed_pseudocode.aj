FUNCTION LevelOrderTraversal ACCEPTS(root)
    IF root == NULL THEN
        RETURN EMPTY LIST

    ENDIF
    result <- EMPTY LIST
    queue <- CALL create_queue()
    CALL ENQUEUE(queue, root)
    WHILE NOT CALL queue_is_empty(queue) DO
        level_size <- CALL queue_size(queue)
        current_level <- EMPTY LIST

        FOR i <- IN RANGE 1 TO (level_size) + 1 DO
            node <- CALL DEQUEUE(queue)
            APPEND node.value TO current_level

            IF node.left != NULL THEN
                CALL ENQUEUE(queue, node.left)
            ENDIF
            IF node.right != NULL THEN
                CALL ENQUEUE(queue, node.right)
            ENDIF
        ENDFOR

        APPEND current_level TO result
    ENDWHILE

    RETURN result
ENDFUNCTION