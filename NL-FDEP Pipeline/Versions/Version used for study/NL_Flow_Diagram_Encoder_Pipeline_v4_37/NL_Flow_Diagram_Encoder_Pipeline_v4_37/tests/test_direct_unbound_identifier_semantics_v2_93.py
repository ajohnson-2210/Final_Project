from aj_parser import AJParserFacade


def parse(source: str):
    return AJParserFacade().parse(source)


def test_direct_assignment_rhs_must_be_bound():
    result = parse('''FUNCTION demo ACCEPTS()\n    value <- missingValue\n    RETURN value\nENDFUNCTION\n''')
    assert not result.success
    assert "missingValue" in result.error
    assert "read before declaration or assignment" in result.error
    assert result.report.stages[-1].name == "STATIC_SEMANTIC_ANALYSIS"


def test_direct_return_value_must_be_bound():
    result = parse('''FUNCTION demo ACCEPTS()\n    RETURN missingResult\nENDFUNCTION\n''')
    assert not result.success
    assert "missingResult" in result.error


def test_direct_output_value_must_be_bound():
    result = parse('''FUNCTION demo ACCEPTS()\n    OUTPUT missingValue\n    RETURN NONE\nENDFUNCTION\n''')
    assert not result.success
    assert "missingValue" in result.error


def test_parameter_is_valid_direct_binding():
    result = parse('''FUNCTION demo ACCEPTS(value)\n    copy <- value\n    RETURN copy\nENDFUNCTION\n''')
    assert result.success, result.error


def test_prior_assignment_is_valid_direct_binding():
    result = parse('''FUNCTION demo ACCEPTS()\n    value <- 1\n    copy <- value\n    RETURN copy\nENDFUNCTION\n''')
    assert result.success, result.error


def test_enclosing_binding_is_visible_to_nested_function():
    result = parse('''FUNCTION outer ACCEPTS(seed)\n    value <- seed\n    FUNCTION inner ACCEPTS()\n        RETURN value\n    ENDFUNCTION\n    RETURN value\nENDFUNCTION\n''')
    assert result.success, result.error


def test_compound_expression_validation_is_deliberately_not_broadened_in_v2_93():
    # v2.93 implements the approved direct-read subset only.  A fuller\n    # definite-assignment pass is a separate audit/change candidate.
    result = parse('''FUNCTION demo ACCEPTS(value)\n    RETURN value + unresolved\nENDFUNCTION\n''')
    assert result.success, result.error
