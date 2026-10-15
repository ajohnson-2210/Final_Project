from aj_parser import AJParserFacade


def parse(source: str):
    return AJParserFacade().parse(source)


def test_explicit_integer_plus_string_is_static_failure():
    result=parse('''
FUNCTION demo ACCEPTS()
    value <- INTEGER(5) + STRING("two")
    RETURN value
ENDFUNCTION
''')
    assert not result.success
    assert "Operator '+' has incompatible operand types INTEGER and STRING" in result.error


def test_explicit_numeric_mixture_remains_compatible():
    result=parse('''
FUNCTION demo ACCEPTS()
    value <- INTEGER(5) + FLOAT(2.5)
    RETURN value
ENDFUNCTION
''')
    assert result.success, result.error


def test_explicit_string_concatenation_remains_compatible():
    result=parse('''
FUNCTION demo ACCEPTS()
    value <- STRING("a") + STRING("b")
    RETURN value
ENDFUNCTION
''')
    assert result.success, result.error


def test_if_and_while_require_known_boolean_conditions():
    bad_if=parse('''
FUNCTION demo ACCEPTS()
    IF INTEGER(1) THEN
        RETURN 1
    ENDIF
    RETURN 0
ENDFUNCTION
''')
    assert not bad_if.success
    assert 'IF condition must be BOOLEAN, found INTEGER' in bad_if.error

    bad_while=parse('''
FUNCTION demo ACCEPTS()
    WHILE STRING("yes") DO
        RETURN 1
    ENDWHILE
    RETURN 0
ENDFUNCTION
''')
    assert not bad_while.success
    assert 'WHILE condition must be BOOLEAN, found STRING' in bad_while.error


def test_comparison_expression_is_boolean_condition():
    result=parse('''
FUNCTION demo ACCEPTS(a, b)
    IF a < b THEN
        RETURN 1
    ENDIF
    RETURN 0
ENDFUNCTION
''')
    assert result.success, result.error


def test_typed_parameter_supplies_static_operand_evidence():
    bad=parse('''
FUNCTION demo ACCEPTS(value AS STRING)
    RETURN value + INTEGER(1)
ENDFUNCTION
''')
    assert not bad.success
    assert "Operator '+' has incompatible operand types STRING and INTEGER" in bad.error

    unknown=parse('''
FUNCTION demo ACCEPTS(value)
    RETURN value + INTEGER(1)
ENDFUNCTION
''')
    assert unknown.success, unknown.error


def test_assignment_of_known_literal_propagates_narrow_type_evidence():
    result=parse('''
FUNCTION demo ACCEPTS()
    flag <- INTEGER(1)
    IF flag THEN
        RETURN 1
    ENDIF
    RETURN 0
ENDFUNCTION
''')
    assert not result.success
    assert 'IF condition must be BOOLEAN, found INTEGER' in result.error


def test_known_list_requires_integer_index_but_dictionary_and_unknown_receiver_do_not():
    literal_bad=parse('''
FUNCTION demo ACCEPTS()
    values <- LIST [INTEGER(1), INTEGER(2)]
    RETURN values[STRING("x")]
ENDFUNCTION
''')
    assert not literal_bad.success
    assert 'LIST index must be INTEGER, found STRING' in literal_bad.error

    typed_bad=parse('''
FUNCTION demo ACCEPTS(values AS LIST)
    RETURN values[STRING("x")]
ENDFUNCTION
''')
    assert not typed_bad.success
    assert 'LIST index must be INTEGER, found STRING' in typed_bad.error

    dictionary_ok=parse('''
FUNCTION demo ACCEPTS(values AS DICTIONARY)
    RETURN values[STRING("x")]
ENDFUNCTION
''')
    assert dictionary_ok.success, dictionary_ok.error

    unknown_ok=parse('''
FUNCTION demo ACCEPTS(values)
    RETURN values[STRING("x")]
ENDFUNCTION
''')
    assert unknown_ok.success, unknown_ok.error


def test_homogeneous_typed_list_rejects_explicit_incompatible_item():
    result=parse('''
FUNCTION demo ACCEPTS()
    values <- LIST OF INTEGER [INTEGER(1), STRING("two")]
    RETURN values
ENDFUNCTION
''')
    assert not result.success
    assert 'LIST OF INTEGER contains incompatible STRING value' in result.error


def test_typed_property_supplies_explicit_this_type_evidence():
    good=parse('''
CLASS Demo
    PROPERTY flag AS BOOLEAN
    METHOD check ACCEPTS()
        IF THIS.flag THEN
            RETURN 1
        ENDIF
        RETURN 0
    ENDMETHOD
ENDCLASS
''')
    assert good.success, good.error

    bad=parse('''
CLASS Demo
    PROPERTY flag AS INTEGER
    METHOD check ACCEPTS()
        IF THIS.flag THEN
            RETURN 1
        ENDIF
        RETURN 0
    ENDMETHOD
ENDCLASS
''')
    assert not bad.success
    assert 'IF condition must be BOOLEAN, found INTEGER' in bad.error


def test_branch_disagreement_drops_inferred_type_instead_of_guessing():
    result=parse('''
FUNCTION demo ACCEPTS(flag AS BOOLEAN)
    IF flag THEN
        value <- INTEGER(1)
    ELSE
        value <- STRING("one")
    ENDIF
    RETURN CALL external_helper(value)
ENDFUNCTION
''')
    assert result.success, result.error


def test_known_dictionary_rejects_definitely_unhashable_collection_key():
    for key in ('EMPTY LIST', 'EMPTY SET', 'EMPTY DICTIONARY'):
        result=parse(f'''
FUNCTION demo ACCEPTS(values AS DICTIONARY)
    RETURN values[{key}]
ENDFUNCTION
''')
        assert not result.success
        assert 'DICTIONARY key has definitely unhashable type' in result.error


def test_known_dictionary_allows_explicit_hashable_scalar_key():
    result=parse('''
FUNCTION demo ACCEPTS(values AS DICTIONARY)
    RETURN values[STRING("name")]
ENDFUNCTION
''')
    assert result.success, result.error


def test_collection_operations_reject_statically_known_incompatible_receivers():
    bad_append=parse('''
FUNCTION demo ACCEPTS()
    text <- EMPTY STRING
    APPEND STRING("x") TO text
    RETURN text
ENDFUNCTION
''')
    assert not bad_append.success
    assert 'APPEND requires LIST or SET collection, found STRING' in bad_append.error

    bad_remove=parse('''
FUNCTION demo ACCEPTS()
    values <- EMPTY SET
    REMOVE FIRST ITEM FROM values
    RETURN values
ENDFUNCTION
''')
    assert not bad_remove.success
    assert 'REMOVE FIRST/LAST requires LIST collection, found SET' in bad_remove.error


def test_collection_operations_keep_unknown_receiver_unchecked_and_set_append_valid():
    unknown=parse('''
FUNCTION demo ACCEPTS(values, item)
    APPEND item TO values
    RETURN values
ENDFUNCTION
''')
    assert unknown.success, unknown.error

    set_ok=parse('''
FUNCTION demo ACCEPTS(item)
    values <- EMPTY SET
    APPEND item TO values
    RETURN values
ENDFUNCTION
''')
    assert set_ok.success, set_ok.error
