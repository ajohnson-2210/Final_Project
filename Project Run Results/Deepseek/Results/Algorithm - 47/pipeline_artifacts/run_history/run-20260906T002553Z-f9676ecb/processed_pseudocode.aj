FUNCTION updateInventory ACCEPTS(inventory, transactions)
    FOR EACH transaction IN transactions DO
        itemID <- transaction.itemID
        quantityChange <- transaction.quantity
        COMMENT positive for delivery, negative for purchase
        IF itemID IN inventory THEN
            inventory[itemID] <- inventory[itemID] + quantityChange
        ELSE
            COMMENT Handle new item, maybe set initial stock
            inventory[itemID] <- quantityChange
    COMMENT Ensure no negative inventory (adjust accordingly)
        ENDIF
    ENDFOR
    FOR EACH item IN inventory DO
        IF inventory[item] < 0 THEN
            inventory[item] <- 0
            COMMENT or raise error
        ENDIF
    ENDFOR
    RETURN inventory
ENDFUNCTION