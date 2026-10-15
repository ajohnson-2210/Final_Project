from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _raw_algorithm1():
    return '''BEGIN
    INPUT String1, String2

    IF LENGTH(String1) ≠ LENGTH(String2) THEN
        OUTPUT "Not Anagrams"
    ELSE
        SORT characters of String1
        SORT characters of String2

        IF String1 = String2 THEN
            OUTPUT "Anagrams"
        ELSE
            OUTPUT "Not Anagrams"
        ENDIF
    ENDIF
END
'''


def test_source_a_algorithm1_uses_neutral_wrapper_and_preserves_sort_semantics():
    result = PseudocodeProfileProcessor().process(
        _raw_algorithm1(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )

    assert result.processed_source.startswith(
        "FUNCTION unnamed_function ACCEPTS(String1, String2)"
    )
    assert "FUNCTION PROCESS" not in result.processed_source
    assert "String1 <- INPUT" not in result.processed_source
    assert "String2 <- INPUT" not in result.processed_source
    assert "String1 <- CALL sort_characters(String1)" in result.processed_source
    assert "String2 <- CALL sort_characters(String2)" in result.processed_source
    assert "IF String1 == String2 THEN" in result.processed_source

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "def unnamed_function(String1, String2):" in compiled.source_code
    assert "String1 = ''.join(sorted(String1))" in compiled.source_code
    assert "String2 = ''.join(sorted(String2))" in compiled.source_code


def test_source_named_function_is_not_rewrapped_or_renamed():
    source = '''FUNCTION Compare ACCEPTS(String1, String2)
    IF String1 == String2 THEN
        OUTPUT STRING("Same")
    ENDIF
ENDFUNCTION
'''
    result = PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    assert "FUNCTION Compare ACCEPTS(String1, String2)" in result.processed_source
    assert "FUNCTION unnamed_function" not in result.processed_source
    assert "FUNCTION PROCESS" not in result.processed_source


def _lossy_algorithm1():
    return '''BEGIN
    INPUT String1, String2

    IF LENGTH(String1) ? LENGTH(String2) THEN
        OUTPUT "Not Anagrams"
    ELSE
        SORT characters of String1
        SORT characters of String2

        IF String1 = String2 THEN
            OUTPUT "Anagrams"
        ELSE
            OUTPUT "Not Anagrams"
        ENDIF
    ENDIF
END
'''


def test_source_a_algorithm1_lossy_not_equal_is_recovered_only_upstream():
    result = PseudocodeProfileProcessor().process(
        _lossy_algorithm1(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )

    recoveries = [t for t in result.transformations if t.rule == "GC194:A1_LENGTH_NE"]
    assert len(recoveries) == 1
    assert "?" in recoveries[0].source
    assert "≠" in recoveries[0].target
    assert "?" not in result.processed_source
    assert "≠" not in result.processed_source
    assert "IF LENGTH OF String1 != LENGTH OF String2 THEN" in result.processed_source

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error


def test_source_a_algorithm1_authoritative_not_equal_bypasses_lossy_recovery():
    result = PseudocodeProfileProcessor().process(
        _raw_algorithm1(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    assert all(not t.rule.startswith("GC194:") for t in result.transformations)
    assert "IF LENGTH OF String1 != LENGTH OF String2 THEN" in result.processed_source


def test_algorithm1_relational_recovery_is_not_generic_question_mark_support():
    source = '''BEGIN
    INPUT Left, Right
    IF LENGTH(Left) ? LENGTH(Right) THEN
        OUTPUT "Different"
    ENDIF
END
'''
    result = PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    assert all(not t.rule.startswith("GC194:") for t in result.transformations)
    assert "?" in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success
