FUNCTION unnamed_function ACCEPTS(Root)
        Queue <- CALL create_queue()
        CALL ENQUEUE(Queue, Root)
        WHILE NOT CALL queue_is_empty(Queue) DO
            Node <- CALL DEQUEUE(Queue)
            OUTPUT Node.Value
            IF Node.Left != NULL THEN
                CALL ENQUEUE(Queue, Node.Left)
            ENDIF
            IF Node.Right != NULL THEN
                CALL ENQUEUE(Queue, Node.Right)
            ENDIF
        ENDWHILE
ENDFUNCTION