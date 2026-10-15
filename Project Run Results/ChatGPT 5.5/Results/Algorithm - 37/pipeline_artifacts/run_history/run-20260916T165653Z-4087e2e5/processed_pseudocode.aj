    PUSH(Item)
        Top <- Top + 1
        Stack[Top] <- Item

    POP()
        IF Top = -1 THEN
            OUTPUT "Stack Empty"
        ELSE
            Item <- Stack[Top]
            Top <- Top - 1
            OUTPUT Item
        ENDIF

    PEEK()
        IF Top ≠ -1 THEN
            OUTPUT Stack[Top]
        ENDIF
END