FUNCTION unnamed_function ACCEPTS(Matrix, N)
        CALL transpose_in_place(Matrix)
        FOR EACH Row IN Matrix DO
            CALL reverse_list(Row)
        ENDFOR

        OUTPUT Matrix
ENDFUNCTION