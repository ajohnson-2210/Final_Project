from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_c_ALGORITHM_17 = '''FUNCTION sumAndAverage(list):
    sum = 0
    FOR each num in list:
        sum = sum + num
    average = sum / length(list)
    RETURN (sum, average)
'''


def test_source_c_algorithm17_uses_general_parenthesised_tuple_return_recovery():
    result = PseudocodeProfileProcessor().process(
        source_c_ALGORITHM_17,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )

    assert "FUNCTION sumAndAverage ACCEPTS(__reserved_keyword__List)" in result.processed_source
    assert "RETURN TUPLE(sum, average)" in result.processed_source
    assert "CALL RETURN" not in result.processed_source

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))

    namespace = {}
    exec(compiled.source_code, namespace)
    assert namespace["sumAndAverage"]([2, 4, 6]) == (12, 4.0)
