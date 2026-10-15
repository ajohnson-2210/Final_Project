FUNCTION CoreferenceResolution ACCEPTS(text)
    tokens, pos_tags = CALL TokenizeAndTag(text)
    entities <- CALL ExtractNamedEntities(tokens, pos_tags)
    pronouns <- CALL ExtractPronouns(tokens, pos_tags)

    resolved_text <- text
    FOR EACH pronoun IN pronouns DO
        antecedent <- CALL FindMostCompatibleEntity(pronoun, entities
        search_window <- 2_sentences)
        IF antecedent != NULL THEN
            CALL ReplaceInText(resolved_text, pronoun, antecedent.name)
        ENDIF
    ENDFOR

    RETURN resolved_text
ENDFUNCTION