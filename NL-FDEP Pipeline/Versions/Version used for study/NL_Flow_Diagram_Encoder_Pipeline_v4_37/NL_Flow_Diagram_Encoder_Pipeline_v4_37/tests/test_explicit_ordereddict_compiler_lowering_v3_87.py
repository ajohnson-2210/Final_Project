from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _compile(source: str):
    processed = PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    parsed = AJParserFacade().parse(processed.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success, compiled.message
    return processed.processed_source, compiled.source_code


def test_explicit_ordereddict_constructor_is_preserved_in_aj_and_lowered_to_dictionary():
    canonical, python_source = _compile(
        """FUNCTION make ACCEPTS()
    cache <- orderedDict()
    RETURN cache
ENDFUNCTION
"""
    )
    assert "cache <- CALL orderedDict()" in canonical
    assert "CALL create_ordered_dictionary()" not in canonical
    assert "cache = {}" in python_source
    assert "OrderedDict" not in python_source

    namespace = {}
    exec(python_source, namespace)
    value = namespace["make"]()
    assert isinstance(value, dict)


def test_explicit_ordereddict_is_key_value_dictionary_at_runtime():
    canonical, python_source = _compile(
        """FUNCTION make ACCEPTS()
    cache <- orderedDict()
    cache[STRING("b")] <- 2
    cache[STRING("a")] <- 1
    RETURN cache
ENDFUNCTION
"""
    )
    assert "cache <- CALL orderedDict()" in canonical
    namespace = {}
    exec(python_source, namespace)
    value = namespace["make"]()
    assert value == {"b": 2, "a": 1}


def test_generic_ordered_dictionary_phrase_keeps_dict_backing():
    canonical, python_source = _compile(
        """FUNCTION make ACCEPTS()
    cache <- ordered dictionary
    RETURN cache
ENDFUNCTION
"""
    )
    assert "cache <- CALL create_ordered_dictionary()" in canonical
    assert "cache = {}" in python_source
    assert "OrderedDict" not in python_source


def test_plain_dictionary_remains_plain_dictionary():
    canonical, python_source = _compile(
        """FUNCTION make ACCEPTS()
    cache <- empty dictionary
    RETURN cache
ENDFUNCTION
"""
    )
    assert "cache <- EMPTY DICTIONARY" in canonical
    assert "cache = {}" in python_source
    assert "OrderedDict" not in python_source
