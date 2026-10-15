from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def test_explicit_negative_infinity_remains_supported_by_existing_rule():
    source = '''FUNCTION choose ACCEPTS(value)\n    floorValue = -infinity\n    RETURN floorValue\nENDFUNCTION\n'''
    result = _process(source)
    assert 'floorValue <- CALL negative_infinity()' in result.processed_source
    assert sum(t.rule == 'GC151' for t in result.transformations) == 1
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error


def test_question_mark_placeholder_is_not_a_global_negative_infinity_alias():
    source = '''FUNCTION choose ACCEPTS(value)\n    floorValue = -?\n    RETURN floorValue\nENDFUNCTION\n'''
    result = _process(source)
    assert '-?' in result.processed_source
    assert all(t.rule not in {'GC151', 'GC185'} for t in result.transformations)
    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success


def test_plain_question_mark_elsewhere_is_not_reclassified():
    source = '''FUNCTION keep ACCEPTS(value)\n    result = ?\n    RETURN result\nENDFUNCTION\n'''
    result = _process(source)
    assert '?' in result.processed_source
    assert all(t.rule not in {'GC151', 'GC185'} for t in result.transformations)
    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success
