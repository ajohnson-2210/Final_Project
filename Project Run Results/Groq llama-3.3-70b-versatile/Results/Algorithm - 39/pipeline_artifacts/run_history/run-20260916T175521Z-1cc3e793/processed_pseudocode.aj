FUNCTION HAS_CYCLE ACCEPTS(head)
  tortoise <- head
  hare <- head
  WHILE tortoise != NULL AND hare != NULL AND hare.next != NULL DO
    tortoise <- tortoise.next
    hare <- hare.next.next
    IF tortoise == hare THEN
      RETURN BOOLEAN(True)
    ENDIF
  ENDWHILE
  RETURN BOOLEAN(False)
ENDFUNCTION