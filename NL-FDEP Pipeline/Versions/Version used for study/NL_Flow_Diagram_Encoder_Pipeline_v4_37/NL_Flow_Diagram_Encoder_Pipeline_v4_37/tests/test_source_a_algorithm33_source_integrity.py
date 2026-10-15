from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _authoritative_algorithm33() -> str:
    return '''BEGIN
    INPUT Number

    Low ← 0
    High ← Number
    Answer ← 0

    WHILE Low ≤ High
        Mid ← (Low + High) DIV 2

        IF Mid × Mid = Number THEN
            OUTPUT Mid
            STOP
        ELSE IF Mid × Mid < Number THEN
            Answer ← Mid
            Low ← Mid + 1
        ELSE
            High ← Mid - 1
        ENDIF
    ENDWHILE

    OUTPUT Answer
END
'''


def _lossy_algorithm33() -> str:
    return '''BEGIN
    INPUT Number

    Low ? 0
    High ? Number
    Answer ? 0

    WHILE Low ? High
        Mid ? (Low + High) DIV 2

        IF Mid × Mid = Number THEN
            OUTPUT Mid
            STOP
        ELSE IF Mid × Mid < Number THEN
            Answer ? Mid
            Low ? Mid + 1
        ELSE
            High ? Mid - 1
        ENDIF
    ENDWHILE

    OUTPUT Answer
END
'''


def _process(source: str):
    result = PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    return result, compiled.source_code


def test_algorithm33_authoritative_less_equal_uses_normal_character_rule_only():
    result, python_source = _process(_authoritative_algorithm33())

    assert all(not t.rule.startswith('GC194:') for t in result.transformations)
    assert all(t.rule != 'GC193' for t in result.transformations)
    assert 'WHILE Low <= High DO' in result.processed_source
    assert 'RETURN' in result.processed_source
    assert '?' not in result.processed_source
    assert '≤' not in result.processed_source
    assert 'while (Low <= High):' in python_source


def test_algorithm33_lossy_export_recovers_assignments_generically_and_less_equal_specifically():
    result, python_source = _process(_lossy_algorithm33())

    arrows = [t for t in result.transformations if t.rule == 'GC193']
    relation = [t for t in result.transformations if t.rule == 'GC194:A33_LOW_HIGH_LE']
    assert len(arrows) == 7
    assert len(relation) == 1
    assert '?' in relation[0].source and '≤' in relation[0].target
    assert '?' not in result.processed_source
    assert '≤' not in result.processed_source
    assert 'WHILE Low <= High DO' in result.processed_source
    assert 'while (Low <= High):' in python_source


def test_algorithm33_relational_recovery_is_not_generic_question_mark_support():
    unrelated = '''BEGIN
    INPUT Value
    Low ? 0
    High ? Value
    Answer ? 0
    WHILE Low ? High
        Mid ? (Low + High) DIV 2
        IF Mid * Mid = Value THEN
            OUTPUT Mid
            STOP
        ELSE IF Mid * Mid < Value THEN
            Answer ? Mid
            Low ? Mid + 1
        ELSE
            High ? Mid - 1
        ENDIF
    ENDWHILE
    OUTPUT Answer
END
'''
    result = PseudocodeProfileProcessor().process(
        unrelated, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    assert all(not t.rule.startswith('GC194:') for t in result.transformations)
    assert 'WHILE Low ? High' in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success
