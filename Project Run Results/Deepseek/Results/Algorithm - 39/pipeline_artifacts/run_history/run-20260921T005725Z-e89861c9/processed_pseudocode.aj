FUNCTION hasCycle ACCEPTS(head)
    slow <- head
    fast <- head
    WHILE fast != NULL AND fast.next != NULL DO
        slow <- slow.next
        fast <- fast.next.next
        IF slow == fast THEN
            RETURN BOOLEAN(True)
        ENDIF
    ENDWHILE
    RETURN BOOLEAN(False)
ENDFUNCTION