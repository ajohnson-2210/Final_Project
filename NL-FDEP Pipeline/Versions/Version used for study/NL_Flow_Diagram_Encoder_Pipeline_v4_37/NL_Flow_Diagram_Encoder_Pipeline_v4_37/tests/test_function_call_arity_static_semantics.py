from aj_parser import AJParserFacade


def parse(source: str):
    return AJParserFacade().parse(source)


def test_in_scope_function_rejects_too_few_arguments():
    result = parse('''
FUNCTION add ACCEPTS(a, b)
    RETURN a
ENDFUNCTION
FUNCTION demo ACCEPTS()
    RETURN CALL add(1)
ENDFUNCTION
''')
    assert not result.success
    assert "Function 'add' requires 2 arguments, but 1 was supplied" in result.error


def test_in_scope_function_rejects_too_many_arguments():
    result = parse('''
FUNCTION identity ACCEPTS(value)
    RETURN value
ENDFUNCTION
FUNCTION demo ACCEPTS()
    RETURN CALL identity(1, 2)
ENDFUNCTION
''')
    assert not result.success
    assert "Function 'identity' requires 1 argument, but 2 were supplied" in result.error


def test_matching_sibling_function_arity_passes():
    result = parse('''
FUNCTION add ACCEPTS(a, b)
    RETURN a
ENDFUNCTION
FUNCTION demo ACCEPTS()
    RETURN CALL add(1, 2)
ENDFUNCTION
''')
    assert result.success, result.error


def test_recursive_function_uses_its_declared_signature():
    good = parse('''
FUNCTION countdown ACCEPTS(n)
    IF n == 0 THEN
        RETURN 0
    ENDIF
    RETURN CALL countdown(n)
ENDFUNCTION
''')
    assert good.success, good.error

    bad = parse('''
FUNCTION countdown ACCEPTS(n)
    RETURN CALL countdown()
ENDFUNCTION
''')
    assert not bad.success
    assert "Function 'countdown' requires 1 argument, but 0 were supplied" in bad.error


def test_nested_function_signature_shadows_outer_signature():
    result = parse('''
FUNCTION helper ACCEPTS(a, b)
    RETURN a
ENDFUNCTION
FUNCTION outer ACCEPTS()
    FUNCTION helper ACCEPTS(value)
        RETURN value
    ENDFUNCTION
    RETURN CALL helper(1)
ENDFUNCTION
''')
    assert result.success, result.error


def test_forward_sibling_declaration_is_lexically_resolved():
    result = parse('''
FUNCTION first ACCEPTS()
    RETURN CALL later(1, 2)
ENDFUNCTION
FUNCTION later ACCEPTS(a, b)
    RETURN a
ENDFUNCTION
''')
    assert result.success, result.error


def test_external_undefined_helper_arity_remains_unchecked():
    result = parse('''
FUNCTION demo ACCEPTS(value)
    RETURN CALL external_helper(value, 1, 2)
ENDFUNCTION
''')
    assert result.success, result.error
