FUNCTION CHECK_PASSWORD ACCEPTS(password)
  IF LENGTH OF password < 8 THEN
    RETURN BOOLEAN(False)
  ENDIF
  has_number <- BOOLEAN(False)
  has_uppercase <- BOOLEAN(False)
  FOR EACH c IN password DO
    IF CALL is_number(c) THEN
      has_number <- BOOLEAN(True)
    ELSE IF CALL is_uppercase(c) THEN
      has_uppercase <- BOOLEAN(True)
    ENDIF
  ENDFOR
  IF has_number AND has_uppercase THEN
    RETURN BOOLEAN(True)
  ELSE
    RETURN BOOLEAN(False)
  ENDIF
ENDFUNCTION