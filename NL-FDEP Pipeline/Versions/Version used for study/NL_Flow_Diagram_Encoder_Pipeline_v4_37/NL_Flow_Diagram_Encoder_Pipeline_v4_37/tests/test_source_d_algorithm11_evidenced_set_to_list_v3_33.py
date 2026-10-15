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


def test_source_d_algorithm11_explicit_set_conversion_executes():
    source = '''FUNCTION GetUniqueIPs(ip_list):
    unique_set = empty Set
    FOR EACH ip IN ip_list DO
        ADD ip TO unique_set
    END FOR
    RETURN ConvertSetToList(unique_set)
END FUNCTION
'''
    result = process(source)

    assert any(t.rule == "GC232" for t in result.transformations)
    assert "unique_set <- EMPTY SET" in result.processed_source
    assert "RETURN CALL to_list(unique_set)" in result.processed_source

    compiled = compile_source(result.processed_source)
    assert "return list(unique_set)" in compiled

    namespace = {}
    exec(compiled, namespace)
    output = namespace["GetUniqueIPs"](
        ["10.0.0.1", "10.0.0.2", "10.0.0.1", "10.0.0.3"]
    )
    assert set(output) == {"10.0.0.1", "10.0.0.2", "10.0.0.3"}
    assert len(output) == 3


def test_gc232_refuses_unproven_identifier():
    result = process('''FUNCTION f(values):
    RETURN ConvertSetToList(values)
END FUNCTION
''')
    assert all(t.rule != "GC232" for t in result.transformations)
    assert "CALL ConvertSetToList(values)" in result.processed_source


def test_gc232_does_not_borrow_set_evidence_from_another_function():
    result = process('''FUNCTION first():
    values = empty Set
    RETURN values
END FUNCTION
FUNCTION second(values):
    RETURN ConvertSetToList(values)
END FUNCTION
''')
    assert all(t.rule != "GC232" for t in result.transformations)
    assert "CALL ConvertSetToList(values)" in result.processed_source


def test_gc232_requires_set_evidence_before_the_call():
    result = process('''FUNCTION f():
    result = ConvertSetToList(values)
    values = empty Set
    RETURN result
END FUNCTION
''')
    assert all(t.rule != "GC232" for t in result.transformations)
    assert "CALL ConvertSetToList(values)" in result.processed_source


def test_gc232_direct_reassignment_invalidates_set_evidence():
    result = process('''FUNCTION f():
    values = empty Set
    values = empty List
    RETURN ConvertSetToList(values)
END FUNCTION
''')
    assert all(t.rule != "GC232" for t in result.transformations)
    assert "CALL ConvertSetToList(values)" in result.processed_source


def test_gc232_refuses_member_calls_and_wrong_arity():
    member = process('''FUNCTION f(values, converter):
    values = empty Set
    RETURN converter.ConvertSetToList(values)
END FUNCTION
''')
    multi = process('''FUNCTION f():
    values = empty Set
    RETURN ConvertSetToList(values, 1)
END FUNCTION
''')
    zero = process('''FUNCTION f():
    values = empty Set
    RETURN ConvertSetToList()
END FUNCTION
''')

    for result in (member, multi, zero):
        assert all(t.rule != "GC232" for t in result.transformations)
