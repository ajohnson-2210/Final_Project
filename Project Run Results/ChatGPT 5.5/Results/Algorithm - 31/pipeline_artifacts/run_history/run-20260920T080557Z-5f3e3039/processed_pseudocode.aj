FUNCTION unnamed_function ACCEPTS(Text)
        PREPROCESS Text

        IDENTIFY all nouns
        IDENTIFY all pronouns

        FOR EACH Pronoun
            FIND the most likely matching noun
            LINK Pronoun to Noun
ENDFUNCTION
        ENDFOR

        OUTPUT Linked References
ENDFUNCTION