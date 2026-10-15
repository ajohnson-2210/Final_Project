FUNCTION ARE_ANAGRAMS ACCEPTS(str1, str2)
  str1 <- CALL sort_value(str1)
  str2 <- CALL sort_value(str2)
  IF str1 == str2 THEN
    RETURN BOOLEAN(True)
  ELSE
    RETURN BOOLEAN(False)
  ENDIF
ENDFUNCTION