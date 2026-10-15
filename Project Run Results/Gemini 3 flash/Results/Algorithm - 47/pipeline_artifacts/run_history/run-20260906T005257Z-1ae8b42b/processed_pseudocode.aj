    FOR EACH item IN transactions DO
        IF item.type == STRING("PURCHASE") THEN
            inventory_map[item.id] <- inventory_map[item.id] - item.quantity
        ELSE IF item.type == STRING("DELIVERY") THEN
            inventory_map[item.id] <- inventory_map[item.id] + item.quantity
        ENDIF
    ENDFOR
ENDFUNCTION