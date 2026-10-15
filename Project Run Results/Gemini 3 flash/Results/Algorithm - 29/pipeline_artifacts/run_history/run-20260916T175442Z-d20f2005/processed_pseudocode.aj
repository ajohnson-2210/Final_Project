    processed_corpus <- CALL PreprocessText(corpus)
    X_train, X_test, y_train, y_test = CALL SplitData(processed_corpus, labels)

    vectorizer <- CALL TrainTFIDFVectorizer(X_train)
    X_train_vec <- vectorizer.transform(X_train)

    model <- CALL TrainClassifierModel(X_train_vec, y_train)

    X_test_vec <- vectorizer.transform(X_test)
    predictions <- model.predict(X_test_vec)

    CALL EvaluateModel(predictions, y_test)
ENDFUNCTION