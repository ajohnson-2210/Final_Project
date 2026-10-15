FUNCTION unnamed_function ACCEPTS(a, b)
    a <- a + b
    b <- a - b
    a <- a - b

    RETURN TUPLE(a, b)
ENDFUNCTION