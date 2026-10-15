FUNCTION unnamed_function ACCEPTS(text)
    mentions <- CALL extractNounPhrasesAndPronouns(text)

    FOR EACH pronoun IN mentions DO
        candidates <- CALL filterCompatibleAntecedents(pronoun, mentions)
        antecedent <- CALL scoreAndSelect(candidates)
        CALL link(pronoun, antecedent)

    ENDFOR
    RETURN resolvedMentions
ENDFUNCTION