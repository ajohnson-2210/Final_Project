FUNCTION SUM_AND_AVERAGE ACCEPTS(arr)
  sum <- 0
  FOR EACH num IN arr DO
    sum <- sum + num
  ENDFOR
  average <- sum / LENGTH OF arr
  RETURN CALL list_value(sum, average)
ENDFUNCTION