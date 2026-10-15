FUNCTION unnamed_function ACCEPTS(head)
    slow <- head
    fast <- head

    WHILE fast != null AND fast.next != null DO
        slow <- slow.next
        fast <- fast.next.next

        IF slow == fast THEN
            RETURN BOOLEAN(True)

        ENDIF
    ENDWHILE
    RETURN BOOLEAN(False)
ENDFUNCTION