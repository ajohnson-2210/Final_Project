import pytest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )


@pytest.mark.parametrize(
    'surface',
    [
        'values = array(items)',
        'values <- array(items)',
        'values = CALL array(items)',
        'values <- CALL array(items)',
        'values = ArRaY(items)',
        'values = array(CALL obtain(items))',
    ],
)
def test_free_array_single_argument_preserves_array_conversion(surface):
    source = f'''FUNCTION convert ACCEPTS(items)
    {surface}
    RETURN values
ENDFUNCTION
'''
    result = _process(source)
    assert 'CALL to_array(' in result.processed_source
    assert 'CALL to_list(' not in result.processed_source
    assert any(t.rule == 'GC209' for t in result.transformations)

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert 'list(' in compiled.source_code


@pytest.mark.parametrize(
    'body',
    [
        'values = array()',
        'values = array(a, b)',
        'registry.array(items)',
        'COMMENT example array(items)',
        'OUTPUT STRING("array(items)")',
    ],
)
def test_array_recovery_does_not_guess_outside_free_single_argument_call(body):
    source = f'''FUNCTION keep ACCEPTS(registry, items, a, b)
    {body}
ENDFUNCTION
'''
    result = _process(source)
    assert not any(t.rule == 'GC209' for t in result.transformations)


@pytest.mark.parametrize(
    'surface',
    [
        'RETURN join(values)',
        'RETURN JOIN(values)',
        'RETURN JoIn(values)',
        'result = join(values)',
        'RETURN join(CALL obtain(values))',
    ],
)
def test_free_one_argument_join_gets_explicit_empty_separator(surface):
    source = f'''FUNCTION render ACCEPTS(values)
    {surface}
ENDFUNCTION
'''
    result = _process(source)
    assert 'JOIN(' in result.processed_source
    assert 'EMPTY STRING)' in result.processed_source
    assert any(t.rule == 'GC210' for t in result.transformations)

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error


def test_one_argument_join_compiles_to_empty_string_separator():
    source = '''FUNCTION render ACCEPTS(values)
    RETURN join(values)
ENDFUNCTION
'''
    result = _process(source)
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "return ''.join(values)" in compiled.source_code


@pytest.mark.parametrize(
    'body',
    [
        'RETURN join()',
        'RETURN join(values, separator)',
        'RETURN join(a, b, c)',
        'RETURN formatter.join(values)',
        'COMMENT example join(values)',
        'OUTPUT STRING("join(values)")',
    ],
)
def test_default_join_recovery_does_not_guess_other_arities_members_or_text(body):
    source = f'''FUNCTION keep ACCEPTS(formatter, values, separator, a, b, c)
    {body}
ENDFUNCTION
'''
    result = _process(source)
    assert not any(t.rule == 'GC210' for t in result.transformations)


def test_native_two_argument_join_remains_native_and_does_not_get_defaulted():
    source = '''FUNCTION render ACCEPTS(values, separator)
    RETURN JOIN(values, separator)
ENDFUNCTION
'''
    result = _process(source)
    assert 'RETURN JOIN(values, separator)' in result.processed_source
    assert not any(t.rule == 'GC210' for t in result.transformations)
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
