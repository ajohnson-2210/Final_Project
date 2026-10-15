FUNCTION unnamed_function ACCEPTS(Sentence)
        Words <- CALL split_on_space(Sentence)

        OUTPUT Words
ENDFUNCTION