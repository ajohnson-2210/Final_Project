    ENQUEUE(Item)
        PUSH Item onto Stack1

    DEQUEUE()
        IF Stack2 is empty THEN
            WHILE Stack1 is not empty
                PUSH POP(Stack1) onto Stack2
            ENDWHILE
        ENDIF

        OUTPUT POP(Stack2)
END