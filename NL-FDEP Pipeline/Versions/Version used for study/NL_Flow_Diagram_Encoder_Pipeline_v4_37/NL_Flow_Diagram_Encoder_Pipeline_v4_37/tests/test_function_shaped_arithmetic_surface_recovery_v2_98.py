import pytest

from aj_parser import AJParserFacade
from flow_diagram import FlowDiagramEncoder
from aj_python_compiler import AJPythonCompiler
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


@pytest.mark.parametrize(
    ("surface", "canonical"),
    [
        ("MOD(a, b)", "(a MODULUS b)"),
        ("mod(a, b)", "(a MODULUS b)"),
        ("MODULUS(a, b)", "(a MODULUS b)"),
        ("CALL MOD(a, b)", "(a MODULUS b)"),
        ("CALL MODULUS(a, b)", "(a MODULUS b)"),
        ("FLOOR(a / b)", "(a INTEGER DIVISION b)"),
        ("floor(a / b)", "(a INTEGER DIVISION b)"),
        ("CALL FLOOR(a / b)", "(a INTEGER DIVISION b)"),
    ],
)
def test_free_function_arithmetic_surface_forms_share_existing_canonical_mapping(surface, canonical):
    source = f'''FUNCTION calculate ACCEPTS(a, b)
    value <- {surface}
    RETURN value
ENDFUNCTION
'''
    result = process(source)
    assert f"value <- {canonical}" in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error


def test_numeric_modulus_prepend_to_string_preserves_missing_source_conversion():
    source = '''FUNCTION build ACCEPTS(n)
    text <- EMPTY STRING
    text <- MOD(n, 2) + text
    RETURN text
ENDFUNCTION
'''
    result = process(source)
    assert "text <- (n MODULUS 2) + text" in result.processed_source
    assert "CALL to_string" not in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "text = ((n % 2) + text)" in compiled.source_code
    namespace = {}
    exec(compiled.source_code, namespace)
    with pytest.raises(TypeError, match="int.*str"):
        namespace["build"](1)


@pytest.mark.parametrize(
    "source_fragment",
    [
        "calculator.MOD(a, b)",
        "calculator.FLOOR(a / b)",
        "MYMOD(a, b)",
        "FLOOR(a)",
        "MOD(a, b, c)",
    ],
)
def test_unrelated_or_unsupported_call_shapes_are_not_reclassified(source_fragment):
    source = f'''FUNCTION calculate ACCEPTS(calculator, a, b, c)
    value <- {source_fragment}
    RETURN value
ENDFUNCTION
'''
    result = process(source)
    assert "INTEGER DIVISION" not in result.processed_source
    assert " MODULUS " not in result.processed_source
