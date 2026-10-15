    CALL ENQUEUE(Item)
        PUSH Item onto Stack1

    CALL DEQUEUE()
        IF LENGTH OF Stack2 == 0 THEN
            WHILE LENGTH OF Stack1 > 0 DO
                PUSH CALL POP(Stack1) onto Stack2
            ENDWHILE
        ENDIF

        OUTPUT CALL POP(Stack2)