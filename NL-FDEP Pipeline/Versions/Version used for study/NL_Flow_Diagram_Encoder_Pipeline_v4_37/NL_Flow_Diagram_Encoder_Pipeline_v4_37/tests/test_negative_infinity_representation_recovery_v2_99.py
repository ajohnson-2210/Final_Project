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
        "NEGATIVE_INFINITY",
        "negative_infinity",
        "Negative_Infinity",
        "-infinity",
        "- infinity",
    ],
)
def test_explicit_negative_infinity_assignment_surfaces_share_one_canonical_form(surface):
    source = f'''FUNCTION choose ACCEPTS(value)\n    floorValue = {surface}\n    IF value > floorValue THEN\n        RETURN value\n    ENDIF\n    RETURN floorValue\nENDFUNCTION\n'''
    result = _process(source)
    assert "floorValue <- CALL negative_infinity()" in result.processed_source

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "floorValue = float('-inf')" in compiled.source_code


def test_canonical_arrow_assignment_is_also_accepted():
    source = '''FUNCTION choose ACCEPTS(value)\n    limit <- NEGATIVE_INFINITY\n    RETURN limit\nENDFUNCTION\n'''
    result = _process(source)
    assert "limit <- CALL negative_infinity()" in result.processed_source


def test_unrelated_identifier_is_not_reclassified_as_negative_infinity():
    source = '''FUNCTION keep ACCEPTS(NEGATIVE_INFINITY_VALUE)\n    result <- NEGATIVE_INFINITY_VALUE\n    RETURN result\nENDFUNCTION\n'''
    result = _process(source)
    assert "result <- NEGATIVE_INFINITY_VALUE" in result.processed_source
    assert "CALL negative_infinity()" not in result.processed_source


def test_member_named_negative_infinity_is_not_reclassified():
    source = '''FUNCTION keep ACCEPTS(config)\n    result <- config.NEGATIVE_INFINITY\n    RETURN result\nENDFUNCTION\n'''
    result = _process(source)
    assert "result <- config.NEGATIVE_INFINITY" in result.processed_source
    assert "CALL negative_infinity()" not in result.processed_source


def test_free_bare_negative_infinity_return_is_not_invented_by_assignment_rule():
    source = '''FUNCTION keep ACCEPTS()\n    RETURN NEGATIVE_INFINITY\nENDFUNCTION\n'''
    result = _process(source)
    assert "RETURN NEGATIVE_INFINITY" in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success
