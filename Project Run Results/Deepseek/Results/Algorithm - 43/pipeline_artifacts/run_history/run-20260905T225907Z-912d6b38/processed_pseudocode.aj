FUNCTION towerOfHanoi ACCEPTS(n, source, destination, auxiliary)
    IF n == 1 THEN
        OUTPUT STRING("Move disc 1 from ") + source + STRING(" to ") + destination
        RETURN
    ENDIF
    CALL towerOfHanoi(n-1, source, auxiliary, destination)
    OUTPUT STRING("Move disc ") + n + STRING(" from ") + source + STRING(" to ") + destination
    CALL towerOfHanoi(n-1, auxiliary, destination, source)
ENDFUNCTION