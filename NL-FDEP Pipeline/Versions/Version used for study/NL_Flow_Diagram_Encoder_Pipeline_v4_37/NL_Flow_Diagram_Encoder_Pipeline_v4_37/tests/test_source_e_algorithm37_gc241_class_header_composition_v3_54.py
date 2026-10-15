from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def process(source: str):
    return PseudocodeProfileProcessor().process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)


def test_gc241_preserves_existing_class_constructor_parameters_when_header_is_canonical():
    source = '''CLASS Box ACCEPTS(seed)
    CONSTRUCTOR(seed):
        self.value = seed
    FUNCTION Get():
        RETURN self.value
'''
    result = process(source)
    assert any(t.rule == "GC241" for t in result.transformations)
    assert result.processed_source.startswith("CLASS Box ACCEPTS(seed)")
    assert "CONSTRUCTOR ACCEPTS(seed)" in result.processed_source
    assert "METHOD Get ACCEPTS()" in result.processed_source


def test_gc241_still_refuses_canonical_class_without_both_constructor_and_method():
    source = '''CLASS Box ACCEPTS()
    FUNCTION Get():
        RETURN 1
'''
    result = process(source)
    assert all(t.rule != "GC241" for t in result.transformations)


def test_gc241_still_refuses_top_level_material_after_explicit_canonical_class():
    source = '''CLASS Box ACCEPTS()
    CONSTRUCTOR():
        self.value = 1
    FUNCTION Get():
        RETURN self.value
ENDCLASS
OUTPUT 2
'''
    result = process(source)
    assert all(t.rule != "GC241" for t in result.transformations)
