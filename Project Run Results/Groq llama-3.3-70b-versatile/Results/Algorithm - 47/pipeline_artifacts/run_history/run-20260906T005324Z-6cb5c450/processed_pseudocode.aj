FUNCTION UPDATE_INVENTORY ACCEPTS(purchases, deliveries)
  inventory <- EMPTY LIST
  FOR EACH item IN purchases DO
    IF item IN inventory THEN
      inventory[item] <- inventory[item] - purchases[item]
    ELSE
      inventory[item] <- -purchases[item]
    ENDIF
  ENDFOR
  FOR EACH item IN deliveries DO
    IF item IN inventory THEN
      inventory[item] <- inventory[item] + deliveries[item]
    ELSE
      inventory[item] <- deliveries[item]
    ENDIF
  ENDFOR
  RETURN inventory
ENDFUNCTION