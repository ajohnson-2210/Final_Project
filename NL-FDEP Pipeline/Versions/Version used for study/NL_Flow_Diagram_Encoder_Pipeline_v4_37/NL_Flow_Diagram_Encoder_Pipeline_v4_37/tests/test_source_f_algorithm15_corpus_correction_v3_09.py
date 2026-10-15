from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


# Exact source_f Algorithm 15 occurrence after the approved one-off corpus correction.
CORRECTED_SOURCE = '''INPUT arr

first = -infinity
second = -infinity

FOR num in arr:
    IF num > first:
        second = first
        first = num
    ELSE IF num > second AND num != first:
        second = num

RETURN second
'''

# The TXT conversion artefact is retained only as audit evidence. It must never
# become a generic spelling for negative infinity.
LOSSY_EXPORT_SOURCE = CORRECTED_SOURCE.replace('-infinity', '-?')


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def test_source_f_algorithm15_corrected_corpus_uses_existing_negative_infinity_semantics():
    result = _process(CORRECTED_SOURCE)

    assert result.processed_source.count('CALL negative_infinity()') == 2
    assert sum(t.rule == 'GC151' for t in result.transformations) == 2
    assert all(t.rule != 'GC185' for t in result.transformations)
    assert '-?' not in result.processed_source

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    assert compiled.source_code.count("float('-inf')") == 2

    namespace = {}
    exec(compiled.source_code, namespace)
    fn = namespace['unnamed_function']
    assert fn([1, 5, 3, 4, 2]) == 4
    assert fn([-5, -2, -9, -3]) == -3
    assert fn([7, 7, 6]) == 6


def test_source_f_algorithm15_lossy_question_mark_is_not_interpreted_by_pipeline():
    result = _process(LOSSY_EXPORT_SOURCE)

    assert '-?' in result.processed_source
    assert all(t.rule not in {'GC151', 'GC185'} for t in result.transformations)
    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success
