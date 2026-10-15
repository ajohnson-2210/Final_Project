FUNCTION resolveCoReferences ACCEPTS(text)
    entities <- CALL extractNamedEntities(text)
    mentions <- CALL extractMentions(text)
    COMMENT nouns and pronouns
    FOR EACH pronoun IN mentions DO
        candidates <- CALL findNearestEntities(pronoun, entities)
        bestMatch <- CALL scoreAndRank(candidates, pronoun)
        MAP pronoun TO bestMatch
    ENDFOR
    RETURN coreferenceMap
ENDFUNCTION