FUNCTION AnswerQuestion ACCEPTS(user_query, context_text)
    text_chunks <- CALL ChunkDocument(context_text
    chunk_size <- 500)
    chunk_embeddings <- CALL Embed(text_chunks)
    query_embedding <- CALL Embed(user_query)

    best_chunk <- CALL FindHighestCosineSimilarity(query_embedding, chunk_embeddings)
    answer <- CALL ExtractOrGenerateAnswer(user_query, best_chunk)

    RETURN answer
ENDFUNCTION