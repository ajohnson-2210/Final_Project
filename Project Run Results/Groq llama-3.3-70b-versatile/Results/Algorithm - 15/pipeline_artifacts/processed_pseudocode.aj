FUNCTION SECOND_LARGEST ACCEPTS(arr)
  max <- CALL negative_infinity()
  second_max <- CALL negative_infinity()
  FOR EACH num IN arr DO
    IF num > max THEN
      second_max <- max
      max <- num
    ELSE IF num > second_max AND num != max THEN
      second_max <- num
    ENDIF
  ENDFOR
  RETURN second_max
ENDFUNCTION