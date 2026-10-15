import pytest

from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


@pytest.mark.parametrize(
    "declaration, append_line, expected",
    [
        (
            "results = empty list",
            "results.append(values[indexer.front()])",
            "APPEND values[indexer.front()] TO results",
        ),
        (
            "results <- LIST [1]",
            "results.append(compute(value, other(value)))",
            "APPEND CALL compute(value, CALL other(value)) TO results",
        ),
        (
            "results <- CALL list_value(seed)",
            'results.append(formatValue("(", nested(x)))',
            'APPEND CALL formatValue(STRING("("), CALL nested(x)) TO results',
        ),
    ],
)
def test_nested_append_balancing_uses_explicit_list_evidence(declaration, append_line, expected):
    source = f'''FUNCTION collect ACCEPTS(values, indexer, value, seed, x)
    {declaration}
    {append_line}
    RETURN results
ENDFUNCTION
'''
    result = _process(source)
    assert expected in result.processed_source
    assert any(t.rule == "GC200" for t in result.transformations)


def test_nested_append_without_list_evidence_is_not_reclassified():
    source = '''FUNCTION update ACCEPTS(widget, values, indexer)
    widget.append(values[indexer.front()])
ENDFUNCTION
'''
    result = _process(source)
    assert "APPEND values[indexer[0]] TO widget" not in result.processed_source
    assert not any(t.rule == "GC200" for t in result.transformations)


def test_simple_append_keeps_existing_gc033_path():
    source = '''FUNCTION collect ACCEPTS(value)
    results = empty list
    results.append(value)
    RETURN results
ENDFUNCTION
'''
    result = _process(source)
    assert "APPEND value TO results" in result.processed_source
    assert any(t.rule == "GC033" for t in result.transformations)
    assert not any(t.rule == "GC200" for t in result.transformations)


def test_method_name_containing_append_is_not_reclassified():
    source = '''FUNCTION update ACCEPTS(widget, value)
    widget.appendFormatted(render(value))
ENDFUNCTION
'''
    result = _process(source)
    assert "APPEND" not in result.processed_source.splitlines()[1]
    assert not any(t.rule == "GC200" for t in result.transformations)
