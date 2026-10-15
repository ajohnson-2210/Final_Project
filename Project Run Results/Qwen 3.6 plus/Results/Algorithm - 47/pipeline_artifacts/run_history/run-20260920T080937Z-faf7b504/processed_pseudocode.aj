FUNCTION unnamed_function ACCEPTS(inventoryMap, transactions)
    FOR EACH t IN transactions DO
        IF t.type == STRING("purchase") THEN
            inventoryMap[t.item] <- inventoryMap[t.item] + t.qty

        ENDIF
        IF t.type == STRING("delivery") THEN
            inventoryMap[t.item] <- inventoryMap[t.item] - t.qty

        ENDIF
        IF inventoryMap[t.item] < 0 THEN
            RAISE STRING("Insufficient Stock")

        ENDIF
    ENDFOR
    RETURN inventoryMap
ENDFUNCTION