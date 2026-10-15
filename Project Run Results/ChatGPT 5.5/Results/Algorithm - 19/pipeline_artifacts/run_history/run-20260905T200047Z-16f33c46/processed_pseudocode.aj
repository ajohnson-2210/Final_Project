FUNCTION unnamed_function ACCEPTS(A, B)
        A <- A + B
        B <- A - B
        A <- A - B

        OUTPUT CALL output_values(A, B)
ENDFUNCTION