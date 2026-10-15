from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _raw_algorithm48():
    return '''BEGIN
    INPUT Folder
    INPUT FileType

    FUNCTION Search(CurrentFolder)
        FOR EACH Item IN CurrentFolder
            IF Item is a file AND Item.Type = FileType THEN
                OUTPUT Item
            ELSE IF Item is a folder THEN
                Search(Item)
            ENDIF
        ENDFOR
    END FUNCTION

    Search(Folder)
END
'''


def test_source_a_algorithm48_undefined_file_folder_predicates_remain_expected_failure():
    result = PseudocodeProfileProcessor().process(
        _raw_algorithm48(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )

    # Preserve the model's unresolved predicates.  Do not hide their missing
    # semantics behind invented helper calls or a generated wrapper.
    assert "Item is a file" in result.processed_source
    assert "Item is a folder" in result.processed_source
    assert "CALL is_file" not in result.processed_source
    assert "CALL is_directory" not in result.processed_source
    assert "CALL is_folder" not in result.processed_source
    assert "FUNCTION unnamed_function" not in result.processed_source
    assert "FUNCTION PROCESS" not in result.processed_source
    assert all(t.rule != "GC104" for t in result.transformations)

    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success


def test_source_a_algorithm48_does_not_invent_filesystem_runtime_semantics():
    result = PseudocodeProfileProcessor().process(
        _raw_algorithm48(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    lowered = result.processed_source.lower()
    for forbidden in (
        "os.path",
        "pathlib",
        "listdir",
        "walk(",
        "is_file(",
        "is_directory(",
        "is_folder(",
    ):
        assert forbidden not in lowered
