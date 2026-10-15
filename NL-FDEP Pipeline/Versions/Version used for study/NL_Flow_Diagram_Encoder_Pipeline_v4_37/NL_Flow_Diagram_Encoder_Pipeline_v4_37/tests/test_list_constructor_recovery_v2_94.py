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
    "surface",
    [
        "values = list(items)",
        "values <- list(items)",
        "values = CALL list(items)",
        "values <- CALL list(items)",
        "values = LiSt(items)",
    ],
)
def test_free_list_constructor_surface_is_pipeline_shape_independent(surface):
    source = f'''FUNCTION convert ACCEPTS(items)
    {surface}
    RETURN values
ENDFUNCTION
'''
    result = _process(source)
    assert "values <- CALL to_list(items)" in result.processed_source
    assert "CALL list(" not in result.processed_source

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "values = list(items)" in compiled.source_code


def test_return_list_constructor_is_canonicalised():
    source = '''FUNCTION convert ACCEPTS(items)
    RETURN list(items)
ENDFUNCTION
'''
    result = _process(source)
    assert "RETURN CALL to_list(items)" in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error


def test_nested_single_argument_is_balanced_not_regex_truncated():
    source = '''FUNCTION convert ACCEPTS(items)
    RETURN list(CALL to_set(items))
ENDFUNCTION
'''
    result = _process(source)
    assert "RETURN CALL to_list(CALL to_set(items))" in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error


def test_member_method_named_list_is_not_reclassified():
    source = '''FUNCTION configure ACCEPTS(registry, items)
    registry.list(items)
ENDFUNCTION
'''
    result = _process(source)
    assert "registry.list(items)" in result.processed_source
    assert "CALL to_list(items)" not in result.processed_source


def test_zero_argument_list_call_is_not_guessed():
    source = '''FUNCTION convert ACCEPTS(items)
    values = list()
    RETURN values
ENDFUNCTION
'''
    result = _process(source)
    assert "CALL to_list(" not in result.processed_source


def test_multi_argument_list_call_is_not_guessed():
    source = '''FUNCTION convert ACCEPTS(a, b)
    values = list(a, b)
    RETURN values
ENDFUNCTION
'''
    result = _process(source)
    assert "CALL to_list(" not in result.processed_source


def test_constructor_text_inside_string_or_comment_is_untouched():
    source = '''FUNCTION describe ACCEPTS(items)
    COMMENT example list(items)
    OUTPUT STRING("list(items)")
ENDFUNCTION
'''
    result = _process(source)
    assert "COMMENT example list(items)" in result.processed_source
    assert 'STRING("list(items)")' in result.processed_source
    assert "CALL to_list(items)" not in result.processed_source
