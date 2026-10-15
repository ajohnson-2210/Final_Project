import pytest

from pseudocode_profiles import GenericGrammarNormaliser


@pytest.mark.parametrize(
    "surface",
    ["END CLASS", "end class", "End Class", "END     CLASS"],
)
def test_standalone_spaced_end_class_becomes_canonical_endclass(surface):
    output, transformations = GenericGrammarNormaliser().process(surface)
    assert output == "ENDCLASS"
    assert [item.rule for item in transformations] == ["GC205"]


def test_existing_endclass_is_unchanged_by_gc205():
    output, transformations = GenericGrammarNormaliser().process("ENDCLASS")
    assert output == "ENDCLASS"
    assert "GC205" not in [item.rule for item in transformations]


def test_longer_identifier_is_not_treated_as_class_terminator():
    output, transformations = GenericGrammarNormaliser().process("END CLASSROOM")
    assert output == "END CLASSROOM"
    assert "GC205" not in [item.rule for item in transformations]


def test_quoted_text_is_not_treated_as_class_terminator():
    source = 'OUTPUT "END CLASS"'
    output, transformations = GenericGrammarNormaliser().process(source)
    assert output == source
    assert "GC205" not in [item.rule for item in transformations]


def test_comment_text_is_not_treated_as_class_terminator():
    source = "COMMENT END CLASS"
    output, transformations = GenericGrammarNormaliser().process(source)
    assert output == source
    assert "GC205" not in [item.rule for item in transformations]
