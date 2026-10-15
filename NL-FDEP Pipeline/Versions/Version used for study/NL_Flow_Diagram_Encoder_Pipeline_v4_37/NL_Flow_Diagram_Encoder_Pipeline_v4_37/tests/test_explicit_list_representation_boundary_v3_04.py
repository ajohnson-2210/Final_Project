import pytest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def _compile(processed_source: str) -> str:
    parsed = AJParserFacade().parse(processed_source)
    assert parsed.success, parsed.error
    return AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast)).source_code


def test_explicit_empty_list_is_not_retyped_from_downstream_string_key_use():
    source = '''FUNCTION store(key, value)
    table = []
    table[key] = value
    RETURN table
'''
    processed = _process(source)

    assert "table <- EMPTY LIST" in processed.processed_source
    assert "EMPTY DICTIONARY" not in processed.processed_source

    python_source = _compile(processed.processed_source)
    namespace = {}
    exec(python_source, namespace)
    with pytest.raises(TypeError):
        namespace["store"]("alpha", 7)


def test_explicit_empty_dictionary_remains_dictionary_for_keyed_storage():
    source = '''FUNCTION store(key, value)
    table = empty dictionary
    table[key] = value
    RETURN table
'''
    processed = _process(source)

    assert "table <- EMPTY DICTIONARY" in processed.processed_source
    python_source = _compile(processed.processed_source)
    namespace = {}
    exec(python_source, namespace)
    assert namespace["store"]("alpha", 7) == {"alpha": 7}


def test_explicit_list_indexing_with_integer_index_remains_valid_list_semantics():
    source = '''FUNCTION overwrite(value)
    data = [0]
    data[0] = value
    RETURN data
'''
    processed = _process(source)

    assert "data <- CALL list_value(0)" in processed.processed_source
    python_source = _compile(processed.processed_source)
    namespace = {}
    exec(python_source, namespace)
    assert namespace["overwrite"](9) == [9]
