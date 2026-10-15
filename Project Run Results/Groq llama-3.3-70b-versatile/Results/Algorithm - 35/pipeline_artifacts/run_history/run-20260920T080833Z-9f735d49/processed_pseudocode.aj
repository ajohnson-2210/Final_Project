FUNCTION MEMORY_BUFFER ACCEPTS(capacity)
  buffer <- EMPTY LIST
  timestamps <- {}
  FOR EACH item IN ITEMS DO
    IF LENGTH OF buffer >= capacity THEN
      oldest_item <- CALL FIND_OLDEST_ITEM(buffer, timestamps)
      CALL REMOVE_ITEM(buffer, oldest_item)
    ENDIF
    CALL ADD_ITEM(buffer, item)
    CALL UPDATE_TIMESTAMP(timestamps, item)
  ENDFOR
  RETURN buffer
ENDFUNCTION