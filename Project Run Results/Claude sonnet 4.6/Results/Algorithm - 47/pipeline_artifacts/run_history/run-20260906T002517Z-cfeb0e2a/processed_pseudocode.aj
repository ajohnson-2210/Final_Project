FUNCTION updateInventory ACCEPTS(inventory, transactions)
    FOR EACH transaction IN transactions DO
        item <- transaction.item
        type <- transaction.type
        quantity <- transaction.quantity
        IF item NOT IN inventory THEN
            inventory[item] <- 0
        ENDIF
        IF type == STRING("purchase") THEN
            inventory[item] <- inventory[item] - quantity
        ELSE IF type == STRING("delivery") THEN
            inventory[item] <- inventory[item] + quantity
        ENDIF
        IF inventory[item] < 0 THEN
            OUTPUT STRING("Insufficient stock for ") + item
        ENDIF
    ENDFOR
    RETURN inventory
ENDFUNCTION