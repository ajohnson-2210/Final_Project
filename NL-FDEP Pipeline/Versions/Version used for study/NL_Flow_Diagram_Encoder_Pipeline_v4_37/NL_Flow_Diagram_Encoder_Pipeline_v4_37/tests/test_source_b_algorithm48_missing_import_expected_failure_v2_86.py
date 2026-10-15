from aj_parser import AJParserFacade
from pseudocode_profiles import (
    GenericObviousMismatchNormaliser,
    PseudocodeProfile,
    PseudocodeProfileProcessor,
)


def _source_b_algorithm48():
    return '''FUNCTION findFilesByType(folder, targetExtension):
    results ← []
    FOR each item IN folder.contents:
        IF item is a file AND item.extension == targetExtension THEN
            APPEND item.path TO results
        ELSE IF item is a folder THEN
            results ← results + findFilesByType(item, targetExtension)
    RETURN results
'''


def _process(source):
    return PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )


def test_source_b_algorithm48_is_expected_failure_for_missing_file_predicate_dependency():
    result = _process(_source_b_algorithm48())

    # Preserve the missing dependency evidence instead of fabricating runnable
    # helper calls.  The recursion/properties may still receive structural
    # normalisation, but the environmental predicates remain unresolved.
    assert "item is a file" in result.processed_source
    assert "item is a folder" in result.processed_source
    assert "CALL is_file" not in result.processed_source
    assert "CALL is_directory" not in result.processed_source
    assert all(t.rule != "GC104" for t in result.transformations)

    lowered = result.processed_source.lower()
    for forbidden in (
        "os.path",
        "pathlib",
        "is_file(",
        "is_directory(",
    ):
        assert forbidden not in lowered

    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success


def test_file_folder_predicate_guard_is_source_shape_independent():
    source = '''FUNCTION classify ACCEPTS(entry)
    IF entry is a file THEN
        RETURN 1
    ELSE IF entry is a directory THEN
        RETURN 2
    ENDIF
    RETURN 0
ENDFUNCTION
'''
    result = _process(source)
    assert "entry is a file" in result.processed_source
    assert "entry is a directory" in result.processed_source
    assert "CALL is_file" not in result.processed_source
    assert "CALL is_directory" not in result.processed_source
    assert not AJParserFacade().parse(result.processed_source).success


def test_descriptive_predicates_may_map_when_exact_helpers_are_explicitly_defined():
    source = '''FUNCTION is_file ACCEPTS(entry)
    RETURN TRUE
ENDFUNCTION

FUNCTION is_directory ACCEPTS(entry)
    RETURN FALSE
ENDFUNCTION

FUNCTION classify ACCEPTS(entry)
    IF entry is a file THEN
        RETURN 1
    ELSE IF entry is a folder THEN
        RETURN 2
    ENDIF
    RETURN 0
ENDFUNCTION
'''
    result = _process(source)
    assert "CALL is_file(entry)" in result.processed_source
    assert "CALL is_directory(entry)" in result.processed_source
    assert any(t.rule == "GC104" for t in result.transformations)
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error


def test_explicit_v1_1_member_predicates_are_not_treated_as_missing_dependencies():
    source = '''FUNCTION classify ACCEPTS(entry)
    IF entry.is_file() THEN
        RETURN 1
    ELSE IF entry.is_directory() THEN
        RETURN 2
    ENDIF
    RETURN 0
ENDFUNCTION
'''
    result = _process(source)
    assert "entry.is_file()" in result.processed_source
    assert "entry.is_directory()" in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error


def test_guard_recognises_explicit_exact_helper_import_evidence():
    source = """IMPORT is_file
IMPORT is_directory
IF item is a file THEN
    OUTPUT item
ELSE IF item is a folder THEN
    OUTPUT item
ENDIF
"""
    assert not GenericObviousMismatchNormaliser._has_undefined_environmental_file_type_predicates(source)


def test_partial_import_evidence_does_not_hide_the_other_missing_predicate():
    source = """IMPORT is_file
IF item is a file THEN
    OUTPUT item
ELSE IF item is a folder THEN
    OUTPUT item
ENDIF
"""
    assert GenericObviousMismatchNormaliser._has_undefined_environmental_file_type_predicates(source)
