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


def test_empty_abstract_array_next_index_write_is_not_silently_rewritten_to_growth():
    source = '''CLASS Buffer:
    data = empty array
    cursor = -1

    FUNCTION put(value):
        cursor = cursor + 1
        data[cursor] = value
    ENDCLASS
'''
    processed = _process(source)

    assert "data <- CALL create_array(0, NONE)" in processed.processed_source
    assert "data[cursor] <- value" in processed.processed_source
    assert "APPEND value TO data" not in processed.processed_source
    assert "LENGTH OF data" not in processed.processed_source

    namespace = {}
    exec(_compile(processed.processed_source), namespace)
    buffer = namespace["Buffer"]()
    with pytest.raises(IndexError):
        buffer.put(5)


def test_explicit_append_remains_permitted_when_source_supplies_append_operation():
    source = '''FUNCTION collect(value):
    items = empty list
    items.append(value)
    RETURN items
'''
    processed = _process(source)

    assert "APPEND value TO items" in processed.processed_source
    namespace = {}
    exec(_compile(processed.processed_source), namespace)
    assert namespace["collect"](7) == [7]


def test_indexed_write_into_explicitly_allocated_storage_remains_permitted():
    source = '''FUNCTION overwrite(value):
    data = [0]
    data[0] = value
    RETURN data[0]
'''
    processed = _process(source)

    assert "data[0] <- value" in processed.processed_source
    assert "APPEND value TO data" not in processed.processed_source
    namespace = {}
    exec(_compile(processed.processed_source), namespace)
    assert namespace["overwrite"](11) == 11
