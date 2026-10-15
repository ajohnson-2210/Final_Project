    WHEN Item is accessed
        MARK Item as most recently used
    END

    WHEN New Item is added
        IF Buffer is full THEN
            REMOVE least recently used item
        ENDIF

        INSERT New Item
    END

    OUTPUT Buffer
END