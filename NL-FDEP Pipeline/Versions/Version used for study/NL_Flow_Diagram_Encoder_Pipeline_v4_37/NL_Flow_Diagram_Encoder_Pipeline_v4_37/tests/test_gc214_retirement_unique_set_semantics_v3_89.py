from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def process(source: str):
    return PseudocodeProfileProcessor().process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)


def compile_source(source: str) -> str:
    parsed = AJParserFacade().parse(source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success, compiled.error
    return compiled.source_code


def test_explicit_unique_is_not_erased_when_list_is_already_value_unique():
    source = '''INPUT values
result = []
FOR EACH value IN values DO
    IF value NOT IN result THEN
        APPEND value TO result
    ENDIF
ENDFOR
RETURN unique(result)
'''
    result = process(source)
    assert "RETURN CALL to_set(result)" in result.processed_source
    assert not any(t.rule == "GC214" for t in result.transformations)
    assert any(t.rule == "GC222" for t in result.transformations)
    py = compile_source(result.processed_source)
    ns = {}
    exec(py, ns)
    value = ns["unnamed_function"]([3, 1, 3, 2])
    assert value == {1, 2, 3}
    assert isinstance(value, set)


def test_generic_unique_still_uses_gc222_set_semantics():
    result = process('''INPUT values
RETURN unique(values)
''')
    assert "RETURN CALL to_set(values)" in result.processed_source
    assert any(t.rule == "GC222" for t in result.transformations)
    assert not any(t.rule == "GC214" for t in result.transformations)
