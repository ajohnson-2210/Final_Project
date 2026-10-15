CLASS unnamed_class
    PROPERTY capacity
    PROPERTY cache AS DICTIONARY

    CONSTRUCTOR ACCEPTS(capacity)
        PROPERTY THIS.capacity <- capacity
        PROPERTY THIS.cache <- EMPTY DICTIONARY
    ENDCONSTRUCTOR

    METHOD get ACCEPTS(key)
        IF key in THIS.cache THEN
            CALL moveToFront(THIS.cache, key)
            RETURN THIS.cache[key]
        ELSE
            RETURN null

        ENDIF
    ENDMETHOD

    METHOD put ACCEPTS(key, value)
        IF key in THIS.cache THEN
            CALL moveToFront(THIS.cache, key)
            THIS.cache[key] <- value
        ELSE
            IF LENGTH OF THIS.cache == THIS.capacity THEN
                CALL removeBack(THIS.cache)

            ENDIF
            CALL addToFront(THIS.cache, key, value)
        ENDIF
    ENDMETHOD
ENDCLASS