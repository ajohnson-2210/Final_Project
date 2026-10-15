FUNCTION SUM_EVEN_NUMBERS ACCEPTS(arr)
  sum <- 0
  FOR EACH num IN arr DO
    IF num MODULUS 2 == 0 THEN
      sum <- sum + num
    ENDIF
  ENDFOR
  RETURN sum
ENDFUNCTION