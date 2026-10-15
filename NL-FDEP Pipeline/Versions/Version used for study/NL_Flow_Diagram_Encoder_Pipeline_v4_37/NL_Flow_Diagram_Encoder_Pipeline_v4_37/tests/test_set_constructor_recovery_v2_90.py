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


@pytest.mark.parametrize(
    "assignment",
    [
        "values = set(items)",
        "values <- set(items)",
        "values = CALL set(items)",
        "values <- CALL set(items)",
        "values = SeT(items)",
    ],
)
def test_set_constructor_recovery_is_assignment_and_pipeline_shape_independent(assignment):
    source = f'''FUNCTION convert ACCEPTS(items)
    {assignment}
    RETURN values
ENDFUNCTION
'''
    result = _process(source)
    assert "values <- CALL to_set(items)" in result.processed_source
    assert "CALL set(" not in result.processed_source

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "values = set(items)" in compiled.source_code


def test_unrelated_function_name_is_not_reclassified_as_set_constructor():
    source = '''FUNCTION convert ACCEPTS(items)
    values = dataset(items)
    RETURN values
ENDFUNCTION
'''
    result = _process(source)
    assert "CALL to_set(items)" not in result.processed_source
    assert "CALL dataset(items)" in result.processed_source


def test_member_method_named_set_is_not_reclassified_as_set_constructor():
    source = '''FUNCTION configure ACCEPTS(registry, items)
    registry.set(items)
ENDFUNCTION
'''
    result = _process(source)
    assert "registry.set(items)" in result.processed_source
    assert "CALL to_set(items)" not in result.processed_source
