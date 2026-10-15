from aj_parser import AJParserFacade


def parse(source: str):
    return AJParserFacade().parse(source)


def test_constructor_rejects_direct_value_return():
    result=parse('''
CLASS Demo
    CONSTRUCTOR ACCEPTS()
        RETURN INTEGER(1)
    ENDCONSTRUCTOR
ENDCLASS
''')
    assert not result.success
    assert 'CONSTRUCTOR must not RETURN a value' in result.error


def test_constructor_allows_value_less_return():
    result=parse('''
CLASS Demo
    CONSTRUCTOR ACCEPTS(flag AS BOOLEAN)
        IF flag THEN
            RETURN
        ENDIF
    ENDCONSTRUCTOR
ENDCLASS
''')
    assert result.success, result.error


def test_constructor_rejects_value_return_inside_control_flow():
    result=parse('''
CLASS Demo
    CONSTRUCTOR ACCEPTS(flag AS BOOLEAN)
        IF flag THEN
            RETURN INTEGER(1)
        ELSE
            RETURN
        ENDIF
    ENDCONSTRUCTOR
ENDCLASS
''')
    assert not result.success
    assert 'CONSTRUCTOR must not RETURN a value' in result.error


def test_nested_function_value_return_does_not_count_as_constructor_return():
    result=parse('''
CLASS Demo
    CONSTRUCTOR ACCEPTS()
        FUNCTION helper ACCEPTS(value)
            RETURN value
        ENDFUNCTION
        x <- CALL helper(INTEGER(1))
    ENDCONSTRUCTOR
ENDCLASS
''')
    assert result.success, result.error


def test_method_value_return_remains_valid():
    result=parse('''
CLASS Demo
    CONSTRUCTOR ACCEPTS()
        RETURN
    ENDCONSTRUCTOR
    METHOD value ACCEPTS()
        RETURN INTEGER(1)
    ENDMETHOD
ENDCLASS
''')
    assert result.success, result.error
