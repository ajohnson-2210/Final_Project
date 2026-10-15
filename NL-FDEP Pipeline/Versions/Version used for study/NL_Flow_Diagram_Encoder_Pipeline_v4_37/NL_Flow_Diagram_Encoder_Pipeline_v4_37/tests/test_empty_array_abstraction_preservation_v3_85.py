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


def _compile(source: str) -> str:
    parsed = AJParserFacade().parse(source)
    assert parsed.success, parsed.error
    return AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast)).source_code


def test_assignment_style_empty_array_preserves_array_abstraction():
    processed = _process("""FUNCTION makeArray():
    data = empty array
    RETURN data
""")
    assert "data <- CALL create_array(0, NONE)" in processed.processed_source
    assert "data <- EMPTY LIST" not in processed.processed_source
    python = _compile(processed.processed_source)
    namespace = {}
    exec(python, namespace)
    assert namespace["makeArray"]() == []


def test_command_style_create_empty_array_preserves_array_abstraction():
    processed = _process("""FUNCTION makeArray():
    CREATE empty array data
    RETURN data
""")
    assert "data <- CALL create_array(0, NONE)" in processed.processed_source
    assert "data <- EMPTY LIST" not in processed.processed_source
    python = _compile(processed.processed_source)
    namespace = {}
    exec(python, namespace)
    assert namespace["makeArray"]() == []


def test_create_empty_list_remains_a_list():
    processed = _process("""FUNCTION makeList():
    CREATE empty list data
    RETURN data
""")
    assert "data <- EMPTY LIST" in processed.processed_source
    assert "create_array" not in processed.processed_source


def test_zero_length_array_does_not_invent_growth_capacity():
    processed = _process("""FUNCTION write(value):
    data = empty array
    data[0] = value
    RETURN data
""")
    assert "data <- CALL create_array(0, NONE)" in processed.processed_source
    assert "data[0] <- value" in processed.processed_source
    assert "APPEND value TO data" not in processed.processed_source
    python = _compile(processed.processed_source)
    namespace = {}
    exec(python, namespace)
    with pytest.raises(IndexError):
        namespace["write"](7)
