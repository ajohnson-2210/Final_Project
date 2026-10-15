FUNCTION hanoi ACCEPTS(n, source, target, aux)
    IF n == 1 THEN
        OUTPUT STRING("Move disk 1 from ") + source + STRING(" to ") + target
    ELSE
        CALL hanoi(n-1, source, aux, target)
        OUTPUT STRING("Move disk ") + n + STRING(" from ") + source + STRING(" to ") + target
        CALL hanoi(n-1, aux, target, source)
    ENDIF
ENDFUNCTION