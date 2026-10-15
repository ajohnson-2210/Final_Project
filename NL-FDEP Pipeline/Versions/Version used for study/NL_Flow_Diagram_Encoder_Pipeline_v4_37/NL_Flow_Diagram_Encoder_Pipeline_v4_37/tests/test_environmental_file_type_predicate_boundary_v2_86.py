import pytest

from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _process(source):
    return PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )


@pytest.mark.parametrize(
    "source,file_phrase,directory_phrase",
    [
        (
            '''BEGIN
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
''',
            "Item is a file",
            "Item is a folder",
        ),
        (
            '''FUNCTION findFilesByType(folder, targetExtension):
    results ← []
    FOR each item IN folder.contents:
        IF item is a file AND item.extension == targetExtension THEN
            APPEND item.path TO results
        ELSE IF item is a folder THEN
            results ← results + findFilesByType(item, targetExtension)
    RETURN results
''',
            "item is a file",
            "item is a folder",
        ),
        (
            '''FUNCTION FIND_FILE(directory, file_type)
  files = []
  FOR item IN directory
    IF item IS A FILE AND item.endswith(file_type) THEN
      files += [item]
    ELSE IF item IS A DIRECTORY THEN
      files += FIND_FILE(item, file_type)
    END IF
  END FOR
  RETURN files
END FUNCTION
''',
            "item IS A FILE",
            "item IS A DIRECTORY",
        ),
        (
            '''FUNCTION findFilesByType(directory, fileExtension):
    results = empty list
    FOR each item in directory:
        IF item IS a file:
            IF item.extension == fileExtension:
                results.append(item.path)
        ELSE IF item IS a directory:
            subResults = findFilesByType(item, fileExtension)
            results.extend(subResults)
    RETURN results
''',
            "item IS a file",
            "item IS a directory",
        ),
    ],
    ids=[
        "wrapper-and-output-shape",
        "property-recursion-shape",
        "endswith-and-uppercase-shape",
        "nested-branch-and-member-call-shape",
    ],
)
def test_environmental_predicate_guard_applies_across_corpus_shapes(
    source, file_phrase, directory_phrase
):
    """One semantic rule must protect every corpus/source shape."""
    result = _process(source)

    assert file_phrase in result.processed_source
    assert directory_phrase in result.processed_source
    assert "CALL is_file" not in result.processed_source
    assert "CALL is_directory" not in result.processed_source
    assert all(t.rule != "GC104" for t in result.transformations)
    assert not AJParserFacade().parse(result.processed_source).success


@pytest.mark.parametrize(
    "source",
    [
        '''FUNCTION inspect ACCEPTS(candidate)
    IF candidate is a file THEN
        RETURN 1
    ENDIF
    RETURN 0
ENDFUNCTION
''',
        '''FUNCTION route ACCEPTS(node)
    IF node is a directory THEN
        RETURN 2
    ENDIF
    RETURN 0
ENDFUNCTION
''',
        '''FUNCTION classify ACCEPTS(resource)
    IF resource is a folder THEN
        RETURN 3
    ENDIF
    RETURN 0
ENDFUNCTION
''',
    ],
)
def test_guard_is_not_tied_to_algorithm_name_wrapper_or_variable_name(source):
    result = _process(source)
    assert "CALL is_file" not in result.processed_source
    assert "CALL is_directory" not in result.processed_source
    assert not AJParserFacade().parse(result.processed_source).success
