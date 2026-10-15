FUNCTION TOWER_OF_HANOI ACCEPTS(N)
  FUNCTION MOVE ACCEPTS(n, from_rod, to_rod, aux_rod)
    IF n == 1 THEN
      OUTPUT STRING("Move disk 1 from rod ") + from_rod + STRING(" to rod ") + to_rod
    ELSE
      CALL MOVE(n - 1, from_rod, aux_rod, to_rod)
      OUTPUT STRING("Move disk ") + n + STRING(" from rod ") + from_rod + STRING(" to rod ") + to_rod
      CALL MOVE(n - 1, aux_rod, to_rod, from_rod)
    ENDIF
  ENDFUNCTION
  CALL MOVE(N, STRING("A"), STRING("C"), STRING("B"))
ENDFUNCTION