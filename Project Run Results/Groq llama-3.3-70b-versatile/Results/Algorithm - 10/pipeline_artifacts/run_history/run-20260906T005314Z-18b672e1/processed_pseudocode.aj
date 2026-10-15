FUNCTION COUNT_VOWELS ACCEPTS(text)
  vowels <- CALL list_value(STRING("a"), STRING("e"), STRING("i"), STRING("o"), STRING("u"))
  counts <- EMPTY LIST
  FOR EACH v IN vowels DO
    count <- 0
    FOR EACH c IN text DO
      IF c == v THEN
        count <- count + 1
      ENDIF
    ENDFOR
    APPEND count TO counts
  ENDFOR
  RETURN counts
ENDFUNCTION