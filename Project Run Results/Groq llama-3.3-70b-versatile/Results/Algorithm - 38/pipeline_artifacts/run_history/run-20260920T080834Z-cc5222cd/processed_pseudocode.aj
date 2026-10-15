FUNCTION FIRST_NON_REPEATING_CHARACTER ACCEPTS(s)
  char_count <- EMPTY DICTIONARY
  FOR EACH c IN s DO
    IF c IN char_count THEN
      char_count[c] <- char_count[c] + 1
    ELSE
      char_count[c] <- 1
    ENDIF
  ENDFOR
  FOR EACH c IN s DO
    IF char_count[c] == 1 THEN
      RETURN c
    ENDIF
  ENDFOR
  RETURN NULL
ENDFUNCTION