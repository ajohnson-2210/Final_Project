COMMENT import random

OUTPUT STRING("Inventory System\n")

CLASS Inventory
    PROPERTY items
    PROPERTY qty
    CONSTRUCTOR ACCEPTS(items, qty)
        PROPERTY THIS.items <- items
        PROPERTY THIS.qty <- qty
    ENDCONSTRUCTOR
    METHOD display ACCEPTS()
        OUTPUT STRING("Current Inventory:")
        i <- 0
        WHILE i < LENGTH OF THIS.items DO
            item_name <- THIS.items[i]
            item_quantity <- THIS.qty[i]
            OUTPUT STRING("{item_name} → {item_quantity}")
            i <- i + 1
        ENDWHILE
        OUTPUT STRING("\n")
    ENDMETHOD
    METHOD get_quantity ACCEPTS(item_name)
        i <- 0
        WHILE i < LENGTH OF THIS.items DO
            IF THIS.items[i] == item_name THEN
                RETURN THIS.qty[i]
            ENDIF
            i <- i + 1
        ENDWHILE
        RETURN NONE
    ENDMETHOD
    METHOD set_quantity ACCEPTS(item_name, new_qty)
        i <- 0
        WHILE i < LENGTH OF THIS.items DO
            IF THIS.items[i] == item_name THEN
                THIS.qty[i] <- new_qty
            ENDIF
            i <- i + 1
        ENDWHILE
    ENDMETHOD
    METHOD remove_zero_stock ACCEPTS()
        i <- 0
        WHILE i < LENGTH OF THIS.items DO
            IF THIS.qty[i] == 0 THEN
                removed_item <- THIS.items[i]
                OUTPUT STRING("REMOVED: {removed_item} (stock reached zero)")
                j <- i
                WHILE j < (LENGTH OF THIS.items - 1) DO
                    THIS.items[j] <- THIS.items[j + 1]
                    THIS.qty[j] <- THIS.qty[j + 1]
                    j <- j + 1
                ENDWHILE
                THIS.items.pop()
                THIS.qty.pop()
            ELSE
                i <- i + 1
            ENDIF
        ENDWHILE
    ENDMETHOD
    METHOD update_purchases ACCEPTS(purchase_items, purchase_qty)
        OUTPUT STRING("\nUpdating Inventory After Purchases...\nCustomers")
        i <- 0
        WHILE i < LENGTH OF purchase_items DO
            item <- purchase_items[i]
            amount <- purchase_qty[i]
            j <- 0
            WHILE j < LENGTH OF THIS.items DO
                IF THIS.items[j] == item THEN
                    new_qty <- THIS.qty[j] - amount
                    IF new_qty < 0 THEN
                        new_qty <- 0
                    ENDIF
                    THIS.qty[j] <- new_qty
                    OUTPUT STRING("Purchased: {amount} {item} → New Qty = {new_qty}")
                ENDIF
                j <- j + 1
            ENDWHILE
            i <- i + 1
        ENDWHILE
        OUTPUT STRING("\n")
        THIS.display()
        THIS.remove_zero_stock()
    ENDMETHOD
    METHOD update_deliveries ACCEPTS(delivery_items, delivery_qty)
        OUTPUT STRING("\nUpdating Inventory After Deliveries...\nCompanies")
        i <- 0
        WHILE i < LENGTH OF delivery_items DO
            item <- delivery_items[i]
            amount <- delivery_qty[i]
            j <- 0
            WHILE j < LENGTH OF THIS.items DO
                IF THIS.items[j] == item THEN
                    new_qty <- THIS.qty[j] + amount
                    THIS.qty[j] <- new_qty
                    OUTPUT STRING("Deliverered: {amount} {item} → New Qty = {new_qty}")
                ENDIF
                j <- j + 1
            ENDWHILE
            i <- i + 1
        ENDWHILE
        OUTPUT STRING("\n")
        THIS.display()
        THIS.remove_zero_stock()
    ENDMETHOD
ENDCLASS

item_names <- LIST [STRING("Apples"), STRING("Bananas"), STRING("Oranges"), STRING("Pears"), STRING("Grapes")]
item_qty <- EMPTY LIST
i <- 0
WHILE i < LENGTH OF item_names DO
    qty <- RANDOM INT(10, 100)
    APPEND qty TO item_qty
    i <- i + 1
ENDWHILE
inventory <- CALL Inventory(item_names, item_qty)
OUTPUT STRING("Random Inventory Generated\n")
inventory.display()
purchase_items <- LIST [STRING("Apples"), STRING("Grapes")]
purchase_qty <- LIST [RANDOM INT(1, 10), RANDOM INT(1, 10)]
OUTPUT STRING("Random Purchases Generated:")
i <- 0
WHILE i < LENGTH OF purchase_items DO
    purchase_item <- purchase_items[i]
    purchase_quantity <- purchase_qty[i]
    OUTPUT STRING("{purchase_item} → {purchase_quantity}")
    i <- i + 1
ENDWHILE
inventory.update_purchases(purchase_items, purchase_qty)
delivery_items <- LIST [STRING("Bananas"), STRING("Oranges")]
delivery_qty <- LIST [RANDOM INT(5, 20), RANDOM INT(5, 20)]
OUTPUT STRING("Random Deliveries Generated:")
i <- 0
WHILE i < LENGTH OF delivery_items DO
    delivery_item <- delivery_items[i]
    delivery_quantity <- delivery_qty[i]
    OUTPUT STRING("{delivery_item} → {delivery_quantity}")
    i <- i + 1
ENDWHILE
inventory.update_deliveries(delivery_items, delivery_qty)