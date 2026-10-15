FUNCTION SWAP ACCEPTS(a, b)
  a <- a + b
  b <- a - b
  a <- a - b
  RETURN CALL list_value(a, b)
ENDFUNCTION