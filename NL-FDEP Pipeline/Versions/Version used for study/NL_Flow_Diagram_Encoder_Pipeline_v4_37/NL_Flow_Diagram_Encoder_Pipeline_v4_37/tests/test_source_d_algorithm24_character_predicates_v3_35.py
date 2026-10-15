from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def compile_source(processed_source: str) -> str:
    parsed = AJParserFacade().parse(processed_source)
    assert parsed.success, parsed.error
    return AJPythonCompiler().compile(
        FlowDiagramEncoder().encode(parsed.ast)
    ).source_code


def test_source_d_algorithm24_explicit_character_predicates_execute():
    source = '''FUNCTION ValidatePassword(password):
    IF length(password) < 8 THEN RETURN False

    has_digit = False
    has_uppercase = False

    FOR EACH char IN password DO
        IF IS_DIGIT(char) THEN has_digit = True
        IF IS_UPPERCASE(char) THEN has_uppercase = True
    END FOR

    RETURN (has_digit AND has_uppercase)
END FUNCTION
'''
    result = process(source)

    assert any(t.rule == "GC234" for t in result.transformations)
    assert "CALL is_digit(__reserved_keyword__char)" in result.processed_source
    assert "CALL is_uppercase(__reserved_keyword__char)" in result.processed_source
    assert "IS_DIGIT" not in result.processed_source
    assert "IS_UPPERCASE" not in result.processed_source

    compiled = compile_source(result.processed_source)
    assert "__reserved_keyword__char.isdigit()" in compiled
    assert "__reserved_keyword__char.isupper()" in compiled
    assert "str(__reserved_keyword__char)" not in compiled
    namespace = {}
    exec(compiled, namespace)
    validate = namespace["ValidatePassword"]
    assert validate("Password1") is True
    assert validate("password1") is False
    assert validate("Password") is False
    assert validate("Pass1") is False


def test_gc234_handles_both_exact_free_single_argument_calls():
    source = '''FUNCTION f ACCEPTS(x)
    RETURN IS_DIGIT(x) OR IS_UPPERCASE(x)
ENDFUNCTION
'''
    result = process(source)
    assert any(t.rule == "GC234" for t in result.transformations)
    assert "RETURN CALL is_digit(x) OR CALL is_uppercase(x)" in result.processed_source
    compiled = compile_source(result.processed_source)
    namespace = {}
    exec(compiled, namespace)
    assert namespace["f"]("7") is True
    assert namespace["f"]("Q") is True
    assert namespace["f"]("q") is False


def test_gc234_refuses_declarations_member_calls_and_wrong_arities():
    declaration = process('''FUNCTION IS_DIGIT(x):
    RETURN x
END FUNCTION
''')
    member = process('''FUNCTION f(obj, x):
    RETURN obj.IS_DIGIT(x)
END FUNCTION
''')
    zero = process('''FUNCTION f():
    RETURN IS_UPPERCASE()
END FUNCTION
''')
    multi = process('''FUNCTION f(a, b):
    RETURN IS_DIGIT(a, b)
END FUNCTION
''')

    assert all(t.rule != "GC234" for t in declaration.transformations)
    assert "FUNCTION IS_DIGIT ACCEPTS(x)" in declaration.processed_source
    for result in (member, zero, multi):
        assert all(t.rule != "GC234" for t in result.transformations)


def test_gc234_ignores_quoted_text():
    result = process('''FUNCTION f():
    value = "IS_DIGIT(x) IS_UPPERCASE(x)"
    RETURN value
END FUNCTION
''')
    assert all(t.rule != "GC234" for t in result.transformations)


def test_character_predicate_compiler_does_not_invent_string_cast_v3_91():
    source = """FUNCTION f ACCEPTS(x)
    RETURN CALL is_digit(x)
ENDFUNCTION
"""
    compiled = compile_source(source)
    assert "return x.isdigit()" in compiled
    assert "str(x)" not in compiled

    namespace = {}
    exec(compiled, namespace)
    assert namespace["f"]("123") is True

    try:
        namespace["f"](123)
    except AttributeError:
        pass
    else:
        raise AssertionError("numeric input must not be silently coerced to string")


def test_uppercase_compiler_does_not_invent_string_cast_v3_91():
    source = """FUNCTION f ACCEPTS(x)
    RETURN CALL is_uppercase(x)
ENDFUNCTION
"""
    compiled = compile_source(source)
    assert "return x.isupper()" in compiled
    assert "str(x)" not in compiled

    namespace = {}
    exec(compiled, namespace)
    assert namespace["f"]("Q") is True
    assert namespace["f"]("q") is False

    try:
        namespace["f"](123)
    except AttributeError:
        pass
    else:
        raise AssertionError("numeric input must not be silently coerced to string")
