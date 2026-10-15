FUNCTION REVERSE_STRING ACCEPTS(s)
  reversed <- EMPTY STRING
  FOR i <- IN RANGE LENGTH OF s - 1 TO (0) - 1 STEP -1 DO
    reversed <- reversed + s[i]
  ENDFOR
  RETURN reversed
ENDFUNCTION