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


def test_source_d_algorithm34_explicit_set_conversion_executes():
    source = '''FUNCTION FindUniqueCommonElements(list1, list2):
    set1 = ConvertToSet(list1)
    result_set = empty Set

    FOR EACH item IN list2 DO
        IF item IN set1 THEN
            ADD item TO result_set
        END IF
    END FOR

    RETURN ConvertSetToList(result_set)
END FUNCTION
'''
    result = process(source)

    assert any(t.rule == "GC238" for t in result.transformations)
    assert "set1 <- CALL to_set(list1)" in result.processed_source
    assert "RETURN CALL to_list(result_set)" in result.processed_source

    compiled = compile_source(result.processed_source)
    assert "set1 = set(list1)" in compiled
    assert "return list(result_set)" in compiled

    namespace = {}
    exec(compiled, namespace)
    output = namespace["FindUniqueCommonElements"]([1, 2, 2, 3], [2, 2, 3, 4])
    assert set(output) == {2, 3}
    assert len(output) == 2


def test_gc238_handles_nested_single_argument_expression():
    result = process('''FUNCTION f ACCEPTS(values)
    RETURN ConvertToSet(CALL to_list(values))
ENDFUNCTION
''')
    assert any(t.rule == "GC238" for t in result.transformations)
    assert "RETURN CALL to_set(CALL to_list(values))" in result.processed_source


def test_gc238_refuses_declaration_member_and_wrong_arities():
    declaration = process('''FUNCTION ConvertToSet(value):
    RETURN value
END FUNCTION
''')
    member = process('''FUNCTION f(obj, values):
    RETURN obj.ConvertToSet(values)
END FUNCTION
''')
    zero = process('''FUNCTION f():
    RETURN ConvertToSet()
END FUNCTION
''')
    multi = process('''FUNCTION f(a, b):
    RETURN ConvertToSet(a, b)
END FUNCTION
''')

    assert all(t.rule != "GC238" for t in declaration.transformations)
    assert "FUNCTION ConvertToSet ACCEPTS(value)" in declaration.processed_source
    for result in (member, zero, multi):
        assert all(t.rule != "GC238" for t in result.transformations)


def test_gc238_ignores_quoted_text_and_comments():
    quoted = process('''FUNCTION f():
    value = "ConvertToSet(items)"
    RETURN value
END FUNCTION
''')
    comment = process('''FUNCTION f(items):
    COMMENT ConvertToSet(items)
    RETURN items
END FUNCTION
''')
    assert all(t.rule != "GC238" for t in quoted.transformations)
    assert all(t.rule != "GC238" for t in comment.transformations)
