FUNCTION FIND_PAIRS ACCEPTS(arr, target)
  pairs <- EMPTY LIST
  FOR i <- IN RANGE 0 TO (LENGTH OF arr - 1) + 1 DO
    FOR j <- IN RANGE i + 1 TO (LENGTH OF arr - 1) + 1 DO
      IF arr[i] + arr[j] == target THEN
        APPEND TUPLE(arr[i], arr[j]) TO pairs
      ENDIF
    ENDFOR
  ENDFOR
  RETURN pairs
ENDFUNCTION