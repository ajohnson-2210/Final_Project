Number <- INPUT(STRING("Enter a non-negative integer: "))
Number <- CALL INTEGER(Number)
IF Number < INTEGER(1) THEN
    OUTPUT INTEGER(0)
ELSE
    Total <- INTEGER(0)
    FOR Value <- IN RANGE INTEGER(1) TO Number + INTEGER(1) DO
        Total <- Total + Value
    ENDFOR
    OUTPUT Total
ENDIF
