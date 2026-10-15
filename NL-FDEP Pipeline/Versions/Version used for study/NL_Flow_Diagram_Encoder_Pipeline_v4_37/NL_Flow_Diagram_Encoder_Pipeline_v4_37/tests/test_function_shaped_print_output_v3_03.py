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
    ('source', 'expected'),
    [
        ('PRINT("Value: " + value)', 'OUTPUT STRING("Value: ") + value'),
        ('print("Value: " + value)', 'OUTPUT STRING("Value: ") + value'),
        ('PrInT("Answer: " + value)', 'OUTPUT STRING("Answer: ") + value'),
        ('PRINT(formatValue(a, b))', 'OUTPUT CALL formatValue(a, b)'),
        ('PRINT("a,b")', 'OUTPUT STRING("a,b")'),
    ],
)
def test_function_shaped_print_recovers_one_balanced_expression(source, expected):
    result = _process(source)
    assert result.processed_source == expected
    assert any(item.rule == 'GC206' for item in result.transformations)


@pytest.mark.parametrize(
    'source',
    [
        'PRINT()',
        'PRINT(a, b)',
        'object.PRINT(value)',
        'PRINT(value) trailing',
    ],
)
def test_function_shaped_print_boundary_does_not_claim_unsupported_surfaces(source):
    result = _process(source)
    assert not any(item.rule == 'GC206' for item in result.transformations)


def test_print_text_inside_string_or_comment_is_not_rewritten():
    string_result = _process('OUTPUT "PRINT(value)"')
    comment_result = _process('COMMENT PRINT(value)')
    assert 'PRINT(value)' in string_result.processed_source
    assert 'PRINT(value)' in comment_result.processed_source
    assert not any(item.rule == 'GC206' for item in string_result.transformations)
    assert not any(item.rule == 'GC206' for item in comment_result.transformations)


def test_mixed_literal_identifier_output_lowers_to_fstring_without_cast():
    result = _process('''FUNCTION show(value)\n  PRINT("Value: " + value)\nEND FUNCTION''')
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    assert 'print(f"Value: {value}")' in compiled.source_code
    assert 'str(value)' not in compiled.source_code


def test_non_output_concatenation_is_not_rewritten_as_fstring():
    result = _process('''FUNCTION build(value)\n  message = "Value: " + value\n  RETURN message\nEND FUNCTION''')
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    assignment_lines = [line for line in compiled.source_code.splitlines() if 'message =' in line]
    assert len(assignment_lines) == 1
    assert 'f"' not in assignment_lines[0]
    assert "'Value: '" in assignment_lines[0] or '"Value: "' in assignment_lines[0]
