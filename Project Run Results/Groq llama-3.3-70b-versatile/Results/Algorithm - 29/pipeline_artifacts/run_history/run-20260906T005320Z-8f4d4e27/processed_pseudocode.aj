FUNCTION TEXT_CLASSIFICATION ACCEPTS(text, categories)
  COMMENT Train a machine learning model using the given categories
  model <- CALL TRAIN_MODEL(categories)
  COMMENT Use the trained model to classify the given text
  RETURN CALL CLASSIFY_TEXT(text, model)
ENDFUNCTION