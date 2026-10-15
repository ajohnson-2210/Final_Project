from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def parse(source: str):
    return AJParserFacade().parse(source)


def test_unbound_bare_call_argument_is_rejected():
    result = parse('''FUNCTION demo ACCEPTS(value)\n    answer <- CALL external(value, missingArg)\n    RETURN answer\nENDFUNCTION\n''')
    assert not result.success
    assert "missingArg" in result.error
    assert "read before declaration or assignment" in result.error
    assert result.report.stages[-1].name == "STATIC_SEMANTIC_ANALYSIS"


def test_bound_bare_call_arguments_are_valid_even_when_routine_is_external():
    result = parse('''FUNCTION demo ACCEPTS(value)\n    other <- value\n    answer <- CALL external(value, other)\n    RETURN answer\nENDFUNCTION\n''')
    assert result.success, result.error


def test_undefined_routine_name_is_not_treated_as_value_identifier():
    result = parse('''FUNCTION demo ACCEPTS(value)\n    answer <- CALL undefinedExternal(value)\n    RETURN answer\nENDFUNCTION\n''')
    assert result.success, result.error


def test_compound_call_argument_definite_assignment_remains_out_of_scope():
    result = parse('''FUNCTION demo ACCEPTS(value)\n    answer <- CALL external(value + unresolved)\n    RETURN answer\nENDFUNCTION\n''')
    assert result.success, result.error


def test_member_call_argument_semantics_are_not_broadened_by_v3_13():
    result = parse('''FUNCTION demo ACCEPTS(object)\n    RETURN object.process(unresolved)\nENDFUNCTION\n''')
    assert result.success, result.error


def test_nested_call_checks_its_own_immediate_bare_argument():
    result = parse('''FUNCTION demo ACCEPTS(value)\n    answer <- CALL outer(CALL inner(missingNested))\n    RETURN answer\nENDFUNCTION\n''')
    assert not result.success
    assert "missingNested" in result.error


source_f_30 = '''INPUT corpus

texts = preprocess(corpus)
dtm = buildDocumentTermMatrix(texts)
topics = applyLDA(dtm, numTopics)

RETURN extractTopWords(topics)
'''


def test_exact_source_f_30_normalises_but_fails_static_semantics_on_num_topics():
    processed = PseudocodeProfileProcessor().process(
        source_f_30,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )
    assert "FUNCTION unnamed_function ACCEPTS(corpus)" in processed.processed_source
    assert "topics <- CALL applyLDA(dtm, numTopics)" in processed.processed_source
    assert "RETURN CALL extractTopWords(topics)" in processed.processed_source

    result = parse(processed.processed_source)
    assert not result.success
    assert "numTopics" in result.error
    assert "read before declaration or assignment" in result.error
    assert result.report.stages[-1].name == "STATIC_SEMANTIC_ANALYSIS"
