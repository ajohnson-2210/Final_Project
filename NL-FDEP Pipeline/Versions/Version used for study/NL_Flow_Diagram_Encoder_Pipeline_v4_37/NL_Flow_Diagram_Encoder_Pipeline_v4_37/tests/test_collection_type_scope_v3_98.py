from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder


def _compile(source: str) -> str:
    parsed = AJParserFacade().parse(source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success, compiled.message
    return compiled.source_code


def test_same_named_set_and_list_locals_do_not_share_collection_type():
    source = '''FUNCTION set_side ACCEPTS(x)
    result <- EMPTY SET
    APPEND x TO result
    RETURN result
ENDFUNCTION

FUNCTION list_side ACCEPTS(x)
    result <- EMPTY LIST
    APPEND x TO result
    RETURN result
ENDFUNCTION
'''
    python = _compile(source)
    assert 'def set_side(x):\n    result = set()\n    result.add(x)' in python
    assert 'def list_side(x):\n    result = []\n    result.append(x)' in python
    assert 'result = []\n    result.add(x)' not in python


def test_nested_function_gets_its_own_collection_type_scope():
    source = '''FUNCTION outer ACCEPTS(x)
    result <- EMPTY SET
    APPEND x TO result

    FUNCTION inner ACCEPTS(y)
        result <- EMPTY LIST
        APPEND y TO result
        RETURN result
    ENDFUNCTION

    RETURN result
ENDFUNCTION
'''
    python = _compile(source)
    assert 'result = set()\n    result.add(x)' in python
    assert 'def inner(y):\n        result = []\n        result.append(y)' in python


def test_sibling_method_collection_types_are_independent():
    source = '''CLASS Holder
    METHOD set_side ACCEPTS(x)
        result <- EMPTY SET
        APPEND x TO result
        RETURN result
    ENDMETHOD

    METHOD list_side ACCEPTS(x)
        result <- EMPTY LIST
        APPEND x TO result
        RETURN result
    ENDMETHOD
ENDCLASS
'''
    python = _compile(source)
    assert 'def set_side(self, x):\n        result = set()\n        result.add(x)' in python
    assert 'def list_side(self, x):\n        result = []\n        result.append(x)' in python


def test_nested_function_inherits_unshadowed_enclosing_set_evidence():
    source = '''FUNCTION outer ACCEPTS(x)
    result <- EMPTY SET

    FUNCTION inner ACCEPTS(y)
        APPEND y TO result
    ENDFUNCTION

    APPEND x TO result
    RETURN result
ENDFUNCTION
'''
    python = _compile(source)
    assert 'def inner(y):\n        result.add(y)' in python
    assert 'result.add(x)' in python


def test_nested_parameter_shadows_enclosing_set_evidence():
    source = '''FUNCTION outer ACCEPTS(x)
    result <- EMPTY SET

    FUNCTION inner ACCEPTS(result, y)
        APPEND y TO result
    ENDFUNCTION

    RETURN result
ENDFUNCTION
'''
    python = _compile(source)
    assert 'def inner(result, y):\n        result.append(y)' in python
    assert 'result.add(y)' not in python
