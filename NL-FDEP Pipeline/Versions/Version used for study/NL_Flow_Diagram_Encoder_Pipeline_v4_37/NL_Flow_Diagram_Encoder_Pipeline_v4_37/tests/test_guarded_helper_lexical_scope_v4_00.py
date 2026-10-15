from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder


def _result(source: str):
    parsed = AJParserFacade().parse(source)
    assert parsed.success, parsed.error
    return AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))


def test_nested_guarded_helper_does_not_resolve_sibling_function_call():
    source = '''FUNCTION owner ACCEPTS()
    FUNCTION isSafe ACCEPTS(x)
        RETURN BOOLEAN(TRUE)
    ENDFUNCTION
    RETURN CALL isSafe(1)
ENDFUNCTION

FUNCTION consumer ACCEPTS()
    RETURN CALL isSafe(1)
ENDFUNCTION
'''
    compiled = _result(source)
    assert not compiled.success
    assert compiled.source_code == ''
    assert 'isSafe' in compiled.message


def test_top_level_guarded_helper_resolves_calls_in_other_functions():
    source = '''FUNCTION isSafe ACCEPTS(x)
    RETURN BOOLEAN(TRUE)
ENDFUNCTION

FUNCTION consumer ACCEPTS()
    RETURN CALL isSafe(1)
ENDFUNCTION
'''
    compiled = _result(source)
    assert compiled.success, compiled.message
    assert 'def isSafe(x):' in compiled.source_code
    assert 'return isSafe(1)' in compiled.source_code


def test_enclosing_guarded_helper_is_visible_to_nested_descendant():
    source = '''FUNCTION outer ACCEPTS()
    FUNCTION isSafe ACCEPTS(x)
        RETURN BOOLEAN(TRUE)
    ENDFUNCTION
    FUNCTION inner ACCEPTS()
        RETURN CALL isSafe(1)
    ENDFUNCTION
    RETURN CALL inner()
ENDFUNCTION
'''
    compiled = _result(source)
    assert compiled.success, compiled.message
    assert 'def isSafe(x):' in compiled.source_code
    assert 'def inner():' in compiled.source_code
    assert 'return isSafe(1)' in compiled.source_code
