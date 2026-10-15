FUNCTION LEVEL_ORDER_TRAVERSAL ACCEPTS(root)
  result <- EMPTY LIST
  queue <- CALL list_value(root)
  WHILE LENGTH OF queue > 0 DO
    level <- EMPTY LIST
    FOR i <- IN RANGE 0 TO (LENGTH OF queue - 1) + 1 DO
      node <- REMOVE FIRST ITEM FROM queue
      APPEND node.value TO level
      IF node.left != NULL THEN
        APPEND node.left TO queue
      ENDIF
      IF node.right != NULL THEN
        APPEND node.right TO queue
      ENDIF
    ENDFOR
    APPEND level TO result
  ENDWHILE
  RETURN result
ENDFUNCTION