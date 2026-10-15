from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder


def _compile(canonical: str):
    parsed = AJParserFacade().parse(canonical)
    assert parsed.success, parsed.error
    return AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))


def test_undefined_ordering_helpers_stop_before_python_generation():
    compiled = _compile('''CLASS ordered_cache_class
    PROPERTY cache AS DICTIONARY
    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.cache <- EMPTY DICTIONARY
    ENDCONSTRUCTOR
    METHOD demo ACCEPTS(key, value)
        CALL moveToFront(THIS.cache, key)
        CALL removeBack(THIS.cache)
        CALL addToFront(THIS.cache, key, value)
    ENDMETHOD
ENDCLASS
''')
    assert not compiled.success
    assert compiled.source_code == ""
    assert "moveToFront" in compiled.message
    assert "removeBack" in compiled.message
    assert "addToFront" in compiled.message


def test_explicit_helper_definitions_remove_unresolved_abstraction_block():
    compiled = _compile('''FUNCTION moveToFront ACCEPTS(cache, key)
    RETURN NONE
ENDFUNCTION
FUNCTION removeBack ACCEPTS(cache)
    RETURN NONE
ENDFUNCTION
FUNCTION addToFront ACCEPTS(cache, key, value)
    RETURN NONE
ENDFUNCTION
CLASS ordered_cache_class
    PROPERTY cache AS DICTIONARY
    CONSTRUCTOR ACCEPTS()
        PROPERTY THIS.cache <- EMPTY DICTIONARY
    ENDCONSTRUCTOR
    METHOD demo ACCEPTS(key, value)
        CALL moveToFront(THIS.cache, key)
        CALL removeBack(THIS.cache)
        CALL addToFront(THIS.cache, key, value)
    ENDMETHOD
ENDCLASS
''')
    assert compiled.success, compiled.message
    assert "def moveToFront(cache, key):" in compiled.source_code
    assert "moveToFront(self.cache, key)" in compiled.source_code


def test_unrelated_external_calls_remain_permitted():
    compiled = _compile('''FUNCTION demo ACCEPTS(value)
    RETURN CALL external_operation(value)
ENDFUNCTION
''')
    assert compiled.success, compiled.message
    assert "return external_operation(value)" in compiled.source_code
