FUNCTION COUNT_CHARACTERS ACCEPTS(s)
  counts <- EMPTY DICTIONARY
  FOR EACH c IN s DO
    IF c IN counts THEN
      counts[c] <- counts[c] + 1
    ELSE
      counts[c] <- 1
    ENDIF
  ENDFOR
  RETURN counts
ENDFUNCTION