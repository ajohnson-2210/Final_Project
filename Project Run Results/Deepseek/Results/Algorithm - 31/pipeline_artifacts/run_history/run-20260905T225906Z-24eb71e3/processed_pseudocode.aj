FUNCTION findCoreferences ACCEPTS(text)
    COMMENT Parse the text to identify entities (nouns) and pronouns
    COMMENT Use syntactic and semantic rules (or a trained model)
    COMMENT Cluster mentions that refer to the same entity
    coreferenceChains <- EMPTY LIST of chains
    COMMENT Each chain is a list of mentions (pronouns and nouns) referring to the same entity
    RETURN coreferenceChains
ENDFUNCTION