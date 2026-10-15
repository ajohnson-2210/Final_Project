FUNCTION TOPIC_MODELLING ACCEPTS(corpus)
  COMMENT Use a topic modelling algorithm such as Latent Dirichlet Allocation (LDA) to extract topics
  topics <- CALL EXTRACT_TOPICS(corpus)
  RETURN topics
ENDFUNCTION