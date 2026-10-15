import pytest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder


def compile_source(source: str) -> str:
    parsed = AJParserFacade().parse(source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success, compiled.errors
    return compiled.source_code


def test_one_argument_dictionary_get_lowers_to_indexing_and_raises_for_missing_key():
    python = compile_source('''FUNCTION lookup ACCEPTS(values AS DICTIONARY, key)
    RETURN values.GET(key)
ENDFUNCTION
''')
    assert 'return values[key]' in python
    namespace = {}
    exec(python, namespace)
    assert namespace['lookup']({'x': 7}, 'x') == 7
    with pytest.raises(KeyError):
        namespace['lookup']({}, 'missing')


def test_two_argument_dictionary_get_retains_default_semantics():
    python = compile_source('''FUNCTION lookup ACCEPTS(values AS DICTIONARY, key)
    RETURN values.GET(key, INTEGER(9))
ENDFUNCTION
''')
    assert "return values.get(key, 9)" in python
    namespace = {}
    exec(python, namespace)
    assert namespace['lookup']({}, 'missing') == 9


def test_dictionary_property_one_argument_get_uses_indexing():
    python = compile_source('''CLASS Store
PROPERTY values AS DICTIONARY
CONSTRUCTOR ACCEPTS()
PROPERTY THIS.values <- EMPTY DICTIONARY
ENDCONSTRUCTOR
METHOD lookup ACCEPTS(key)
RETURN THIS.values.GET(key)
ENDMETHOD
ENDCLASS
''')
    assert 'return self.values[key]' in python


def test_unknown_receiver_get_remains_user_method_call():
    python = compile_source('''FUNCTION lookup ACCEPTS(values, key)
    RETURN values.GET(key)
ENDFUNCTION
''')
    assert 'return values.GET(key)' in python
    assert 'return values[key]' not in python


def test_legacy_tilde_get_without_default_preserves_missing_key_error():
    python = compile_source('''FUNCTION lookup ACCEPTS(values AS DICTIONARY, key)
    RETURN values~GET(key)
ENDFUNCTION
''')
    assert 'return values[key]' in python
