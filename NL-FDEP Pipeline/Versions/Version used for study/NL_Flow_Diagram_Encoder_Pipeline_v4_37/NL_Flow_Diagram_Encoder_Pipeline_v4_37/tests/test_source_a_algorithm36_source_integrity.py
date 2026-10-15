from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _authoritative_algorithm36() -> str:
    return '''BEGIN
    INPUT Array, Target

    Low ← 0
    High ← LENGTH(Array) - 1

    WHILE Low ≤ High
        Mid ← (Low + High) DIV 2

        IF Array[Mid] = Target THEN
            OUTPUT Mid
            STOP
        ENDIF

        IF Array[Low] ≤ Array[Mid] THEN
            IF Target ≥ Array[Low] AND Target < Array[Mid] THEN
                High ← Mid - 1
            ELSE
                Low ← Mid + 1
            ENDIF
        ELSE
            IF Target > Array[Mid] AND Target ≤ Array[High] THEN
                Low ← Mid + 1
            ELSE
                High ← Mid - 1
            ENDIF
        ENDIF
    ENDWHILE

    OUTPUT "Not Found"
END
'''


def _lossy_algorithm36() -> str:
    return '''BEGIN
    INPUT Array, Target

    Low ? 0
    High ? LENGTH(Array) - 1

    WHILE Low ? High
        Mid ? (Low + High) DIV 2

        IF Array[Mid] = Target THEN
            OUTPUT Mid
            STOP
        ENDIF

        IF Array[Low] ? Array[Mid] THEN
            IF Target ? Array[Low] AND Target < Array[Mid] THEN
                High ? Mid - 1
            ELSE
                Low ? Mid + 1
            ENDIF
        ELSE
            IF Target > Array[Mid] AND Target ? Array[High] THEN
                Low ? Mid + 1
            ELSE
                High ? Mid - 1
            ENDIF
        ENDIF
    ENDWHILE

    OUTPUT "Not Found"
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


def test_algorithm36_authoritative_relations_need_no_lossy_recovery():
    result, python_source = _process(_authoritative_algorithm36())

    assert all(not t.rule.startswith("GC194:") for t in result.transformations)
    assert all(t.rule != "GC193" for t in result.transformations)
    assert "WHILE Low <= High DO" in result.processed_source
    assert "IF Array[Low] <= Array[Mid] THEN" in result.processed_source
    assert "IF Target >= Array[Low] AND Target < Array[Mid] THEN" in result.processed_source
    assert "IF Target > Array[Mid] AND Target <= Array[High] THEN" in result.processed_source
    assert "?" not in result.processed_source
    assert "while (Low <= High):" in python_source


def test_algorithm36_lossy_export_recovers_assignments_and_four_evidenced_relations():
    result, python_source = _process(_lossy_algorithm36())

    arrows = [t for t in result.transformations if t.rule == "GC193"]
    relations = [t for t in result.transformations if t.rule.startswith("GC194:A36_")]
    assert len(arrows) == 7
    assert len(relations) == 4
    assert sum("≤" in t.target for t in relations) == 3
    assert sum("≥" in t.target for t in relations) == 1
    assert "?" not in result.processed_source
    assert "WHILE Low <= High DO" in result.processed_source
    assert "IF Array[Low] <= Array[Mid] THEN" in result.processed_source
    assert "IF Target >= Array[Low] AND Target < Array[Mid] THEN" in result.processed_source
    assert "IF Target > Array[Mid] AND Target <= Array[High] THEN" in result.processed_source
    assert "while (Low <= High):" in python_source
    assert "Array[Low] <= Array[Mid]" in python_source
    assert "Target >= Array[Low]" in python_source
    assert "Target <= Array[High]" in python_source


def test_algorithm36_relational_recovery_is_not_generic_question_mark_support():
    unrelated = '''BEGIN
    INPUT Values, Wanted
    Low ? 0
    High ? LENGTH(Values) - 1
    WHILE Low ? High
        Mid ? (Low + High) DIV 2
        IF Values[Mid] = Wanted THEN
            OUTPUT Mid
            STOP
        ENDIF
        IF Values[Low] ? Values[Mid] THEN
            OUTPUT Low
        ENDIF
    ENDWHILE
END
'''
    result = PseudocodeProfileProcessor().process(
        unrelated, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    assert all(not t.rule.startswith("GC194:") for t in result.transformations)
    assert "WHILE Low ? High" in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success
