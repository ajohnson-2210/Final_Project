from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


SOURCE = '''FUNCTION commonElements(list1, list2):
    set1 = set(list1)
    result = empty set
    FOR each item in list2:
        IF item IN set1:
            result.add(item)
    RETURN list(result)
'''


def test_source_c_34_is_canonical_aj_constructor_surface_recovery():
    result = PseudocodeProfileProcessor().process(
        SOURCE,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )
    assert "set1 <- CALL to_set(list1)" in result.processed_source
    assert "result <- EMPTY SET" in result.processed_source
    assert "CALL add_to_set(result, item)" in result.processed_source
    assert "RETURN CALL to_list(result)" in result.processed_source

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "return list(result)" in compiled.source_code

    namespace = {}
    exec(compiled.source_code, namespace)
    assert set(namespace["commonElements"]([1, 2, 2, 3], [2, 3, 4, 3])) == {2, 3}


def test_source_c_34_recovery_records_general_gc201_rule():
    result = PseudocodeProfileProcessor().process(
        SOURCE,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )
    assert any(t.rule == "GC201" for t in result.transformations)
