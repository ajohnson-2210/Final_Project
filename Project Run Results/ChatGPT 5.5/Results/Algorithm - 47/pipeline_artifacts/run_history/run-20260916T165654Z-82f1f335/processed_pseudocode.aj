    INPUT Inventory
    INPUT TransactionType
    INPUT Item
    INPUT Quantity

    IF TransactionType = "Purchase" THEN
        Inventory[Item] <- Inventory[Item] - Quantity

    ELSE IF TransactionType = "Delivery" THEN
        Inventory[Item] <- Inventory[Item] + Quantity
    ENDIF

    OUTPUT Inventory
END