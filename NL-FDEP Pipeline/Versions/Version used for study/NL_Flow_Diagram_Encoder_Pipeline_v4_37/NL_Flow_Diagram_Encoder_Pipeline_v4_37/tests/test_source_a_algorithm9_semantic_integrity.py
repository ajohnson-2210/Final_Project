from contextlib import redirect_stdout
from io import StringIO

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _authoritative_algorithm9() -> str:
    return '''BEGIN
    INPUT List, Target

    Found ← FALSE

    FOR i ← 0 TO LENGTH(List)-1
        IF List[i] = Target THEN
            OUTPUT "Found at position", i
            Found ← TRUE
            EXIT FOR
        ENDIF
    ENDFOR

    IF Found = FALSE THEN
        OUTPUT "Target not found"
    ENDIF
END
'''


def _lossy_export_algorithm9() -> str:
    # The stored source_a TXT export lost the authoritative left-arrow glyphs.
    # Question mark is source-recovery evidence here only; it is not AJ syntax.
    return _authoritative_algorithm9().replace('←', '?')


def _compile(source: str):
    result = PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    return result, compiled.source_code


def test_algorithm9_preserves_inclusive_last_index_in_end_exclusive_aj():
    result, python_source = _compile(_authoritative_algorithm9())

    assert 'FOR i <- IN RANGE 0 TO (LENGTH OF __reserved_keyword__List - 1) + 1 DO' in result.processed_source
    assert 'BREAK' in result.processed_source
    assert 'EXIT FOR' not in result.processed_source
    assert '?' not in result.processed_source
    assert 'OUTPUT STRING("Found at position {i}")' in result.processed_source
    assert any(t.rule == 'GC175' for t in result.transformations)
    assert all(t.rule != 'GC173' for t in result.transformations)

    assert 'for i in range(0, len(__reserved_keyword__List)):' in python_source
    assert "print(f'Found at position {i}')" in python_source or 'print(f"Found at position {i}")' in python_source

    namespace = {}
    exec(python_source, namespace)
    output = StringIO()
    with redirect_stdout(output):
        namespace['unnamed_function']([10, 20, 30], 30)
    assert output.getvalue().strip() == "Found at position 2"


def test_algorithm9_lossy_question_mark_is_recovered_before_strict_aj():
    result, _ = _compile(_lossy_export_algorithm9())

    assert '?' not in result.processed_source
    assert '<-' in result.processed_source
    assert any(t.rule == 'GC175' for t in result.transformations)
