    CALL PUSH(Item)
        Top <- Top + 1
        Stack[Top] <- Item

    CALL POP()
        IF Top == -1 THEN
            OUTPUT STRING("Stack Empty")
        ELSE
            Item <- Stack[Top]
            Top <- Top - 1
            OUTPUT Item
        ENDIF

    CALL PEEK()
        IF Top != -1 THEN
            OUTPUT Stack[Top]
        ENDIF