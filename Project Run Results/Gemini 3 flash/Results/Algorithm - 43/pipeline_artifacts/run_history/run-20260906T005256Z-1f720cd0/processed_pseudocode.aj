    IF N == 1 THEN
        OUTPUT STRING("Move disc 1 from ") + source + STRING(" to ") + target
        RETURN
    ENDIF

    CALL TowerOfHanoi(N - 1, source, target, auxiliary)
    OUTPUT STRING("Move disc ") + N + STRING(" from ") + source + STRING(" to ") + target
    CALL TowerOfHanoi(N - 1, auxiliary, source, target)
ENDFUNCTION