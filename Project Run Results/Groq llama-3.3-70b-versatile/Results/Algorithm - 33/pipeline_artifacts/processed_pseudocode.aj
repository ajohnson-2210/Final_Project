FUNCTION SQUARE_ROOT ACCEPTS(n)
  IF n < 0 THEN
    RETURN STRING("ERROR")
  ENDIF
  IF n == 0 OR n == 1 THEN
    RETURN n
  ENDIF
  low <- 0
  high <- n
  WHILE low <= high DO
    mid <- (low + high) / 2
    IF mid * mid <= n THEN
      low <- mid + 1
    ELSE
      high <- mid - 1
    ENDIF
  ENDWHILE
  RETURN high
ENDFUNCTION