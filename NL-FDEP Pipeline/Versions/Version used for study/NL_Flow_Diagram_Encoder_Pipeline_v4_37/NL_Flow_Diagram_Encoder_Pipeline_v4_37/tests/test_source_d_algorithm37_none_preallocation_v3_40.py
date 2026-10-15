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


def test_gc240_array_of_size_uses_user_confirmed_none_preallocation():
    source = '''FUNCTION make_array(capacity):
    arr = Array of size capacity
    RETURN arr
END FUNCTION
'''
    result = process(source)
    assert any(t.rule == "GC240" for t in result.transformations)
    assert "arr <- CALL create_array(capacity, NONE)" in result.processed_source

    compiled = compile_source(result.processed_source)
    assert "arr = [None] * capacity" in compiled

    namespace = {}
    exec(compiled, namespace)
    assert namespace["make_array"](4) == [None, None, None, None]


def test_gc240_recognises_source_d37_member_array_declaration_without_inventing_other_class_repairs():
    source = '''CLASS Stack:
    CONSTRUCTOR(capacity):
        self.arr = Array of size capacity
        self.top_index = -1
END CLASS
'''
    result = process(source)
    assert any(t.rule == "GC240" for t in result.transformations)
    assert "self.arr <- CALL create_array(capacity, NONE)" in result.processed_source


def test_gc240_leaves_explicit_fill_under_existing_gc160_semantics():
    source = '''FUNCTION make_array(capacity):
    arr = Array of size capacity initialized to 0
    RETURN arr
END FUNCTION
'''
    result = process(source)
    assert all(t.rule != "GC240" for t in result.transformations)
    assert "arr <- CALL create_array(capacity, 0)" in result.processed_source
    compiled = compile_source(result.processed_source)
    assert "arr = [0 for _ in range(capacity)]" in compiled


def test_gc240_refuses_non_exact_or_complex_unfilled_array_surface():
    complex_size = process('''FUNCTION f ACCEPTS(capacity)
    arr <- Array of size capacity + 1
    RETURN arr
ENDFUNCTION
''')
    extra_text = process('''FUNCTION f ACCEPTS(capacity)
    arr <- Array of size capacity with reserved slots
    RETURN arr
ENDFUNCTION
''')
    assert all(t.rule != "GC240" for t in complex_size.transformations)
    assert all(t.rule != "GC240" for t in extra_text.transformations)
