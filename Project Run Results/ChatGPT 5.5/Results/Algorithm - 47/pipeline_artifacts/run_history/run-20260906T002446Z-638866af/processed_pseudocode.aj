FUNCTION unnamed_function ACCEPTS(Inventory, TransactionType, Item, Quantity)
    IF TransactionType == STRING("Purchase") THEN
        Inventory[Item] <- Inventory[Item] - Quantity
    ELSE IF TransactionType == STRING("Delivery") THEN
        Inventory[Item] <- Inventory[Item] + Quantity
    ENDIF

    OUTPUT Inventory
ENDFUNCTION