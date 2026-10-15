FUNCTION LONGEST_SUBSTRING ACCEPTS(s)
  max_length <- 0
  start <- 0
  char_index <- EMPTY DICTIONARY
  FOR i <- IN RANGE 0 TO (LENGTH OF s - 1) + 1 DO
    IF s[i] IN char_index AND char_index[s[i]] >= start THEN
      start <- char_index[s[i]] + 1
    ENDIF
    char_index[s[i]] <- i
    max_length <- CALL max(max_length, i - start + 1)
  ENDFOR
  RETURN max_length
ENDFUNCTION