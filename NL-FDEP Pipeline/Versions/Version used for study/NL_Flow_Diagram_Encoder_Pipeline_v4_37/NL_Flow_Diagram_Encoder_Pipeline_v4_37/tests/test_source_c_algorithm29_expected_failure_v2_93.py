from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_c_ALGORITHM_29 = '''FUNCTION trainTextClassifier(documents, labels):
    // Step 1: Preprocess each document (tokenization, stopword removal, stemming)
    // Step 2: Create a vocabulary from the training set
    // Step 3: Convert each document to a feature vector (e.g., TF-IDF)
    // Step 4: Train a classifier (e.g., Naive Bayes, SVM, or Neural Network) on the feature vectors
    model = trainedModel
    RETURN model

FUNCTION predictCategory(model, newText):
    // Preprocess the new text similarly
    // Convert to feature vector
    // Use model to predict the category
    RETURN predictedCategory
'''


def test_source_c_algorithm29_is_expected_static_semantic_failure():
    processed = PseudocodeProfileProcessor().process(
        source_c_ALGORITHM_29,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )

    assert "model <- trainedModel" in processed.processed_source
    assert "RETURN predictedCategory" in processed.processed_source
    assert "COMMENT Step 1: Preprocess" in processed.processed_source

    parsed = AJParserFacade().parse(processed.processed_source)
    assert not parsed.success
    assert "trainedModel" in parsed.error
    assert "read before declaration or assignment" in parsed.error
    assert parsed.report.stages[-1].name == "STATIC_SEMANTIC_ANALYSIS"

    # The pipeline must not fabricate the abstract classifier operations.
    for invented in (
        "tokenize(",
        "TFIDF(",
        "trainClassifier(",
        "predict(",
    ):
        assert invented not in processed.processed_source
