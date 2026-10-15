FUNCTION MAX_IN_WINDOW ACCEPTS(arr, window_size)
  result <- EMPTY LIST
  FOR i <- IN RANGE 0 TO (LENGTH OF arr - window_size) + 1 DO
    max_value <- CALL negative_infinity()
    FOR j <- IN RANGE i TO (i + window_size - 1) + 1 DO
      IF arr[j] > max_value THEN
        max_value <- arr[j]
      ENDIF
    ENDFOR
    APPEND max_value TO result
  ENDFOR
  RETURN result
ENDFUNCTION