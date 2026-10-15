FUNCTION MAX_SUBARRAY_SUM ACCEPTS(arr)
  max_sum <- CALL negative_infinity()
  current_sum <- 0
  FOR EACH num IN arr DO
    current_sum <- CALL max(num, current_sum + num)
    max_sum <- CALL max(max_sum, current_sum)
  ENDFOR
  RETURN max_sum
ENDFUNCTION