FUNCTION gcd ACCEPTS(a, b)
    WHILE b != 0 DO
        temp <- b
        b <- a MODULUS b
        a <- temp
    ENDWHILE
    RETURN a
ENDFUNCTION