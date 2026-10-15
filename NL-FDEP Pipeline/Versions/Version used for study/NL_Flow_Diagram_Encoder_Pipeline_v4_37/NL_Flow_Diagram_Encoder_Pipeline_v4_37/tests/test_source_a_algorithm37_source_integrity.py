from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _authoritative_algorithm37() -> str:
    return """BEGIN
    CREATE Stack
    Top ← -1

    PUSH(Item)
        Top ← Top + 1
        Stack[Top] ← Item

    POP()
        IF Top = -1 THEN
            OUTPUT "Stack Empty"
        ELSE
            Item ← Stack[Top]
            Top ← Top - 1
            OUTPUT Item
        ENDIF

    PEEK()
        IF Top ≠ -1 THEN
            OUTPUT Stack[Top]
        ENDIF
END
"""


def _lossy_algorithm37() -> str:
    return """BEGIN
    CREATE Stack
    Top ? -1

    PUSH(Item)
        Top ? Top + 1
        Stack[Top] ? Item

    POP()
        IF Top = -1 THEN
            OUTPUT "Stack Empty"
        ELSE
            Item ? Stack[Top]
            Top ? Top - 1
            OUTPUT Item
        ENDIF

    PEEK()
        IF Top ? -1 THEN
            OUTPUT Stack[Top]
        ENDIF
END
"""


def test_algorithm37_authoritative_not_equal_needs_no_lossy_relation_recovery():
    result = PseudocodeProfileProcessor().process(
        _authoritative_algorithm37(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    assert all(not t.rule.startswith("GC194:") for t in result.transformations)
    assert all(t.rule != "GC193" for t in result.transformations)
    assert "IF Top != -1 THEN" in result.processed_source
    assert "?" not in result.processed_source
    assert "CREATE Stack" in result.processed_source
    assert "Stack <- EMPTY LIST" not in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success
    assert parsed.ast is None


def test_algorithm37_lossy_export_uses_generic_assignments_and_evidence_table_relation():
    result = PseudocodeProfileProcessor().process(
        _lossy_algorithm37(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    arrows = [t for t in result.transformations if t.rule == "GC193"]
    relations = [t for t in result.transformations if t.rule == "GC194:A37_PEEK_TOP_NE"]
    assert len(arrows) == 5
    assert len(relations) == 1
    assert "?" in relations[0].source and "≠" in relations[0].target
    assert "?" not in result.processed_source
    assert "IF Top != -1 THEN" in result.processed_source
    assert "CREATE Stack" in result.processed_source
    assert "Stack <- EMPTY LIST" not in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success
    assert parsed.ast is None


def test_algorithm37_relation_recovery_is_not_generic_top_question_mark_support():
    unrelated = """BEGIN
    CREATE Values
    Top ? -1
    PEEK()
        IF Top ? -1 THEN
            OUTPUT Values[Top]
        ENDIF
END
"""
    result = PseudocodeProfileProcessor().process(
        unrelated, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    assert all(not t.rule.startswith("GC194:") for t in result.transformations)
    assert "IF Top ? -1 THEN" in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success
