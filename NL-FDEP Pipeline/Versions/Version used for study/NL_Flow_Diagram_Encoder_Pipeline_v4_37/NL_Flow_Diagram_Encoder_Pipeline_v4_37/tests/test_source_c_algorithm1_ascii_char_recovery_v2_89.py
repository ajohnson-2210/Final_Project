from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _source_c_algorithm1_source() -> str:
    return '''FUNCTION areAnagrams(str1, str2):
    IF length(str1) != length(str2):
        RETURN False
    countArray = array of size 256 initialized to 0
    FOR each char in str1:
        countArray[ASCII(char)] = countArray[ASCII(char)] + 1
    FOR each char in str2:
        countArray[ASCII(char)] = countArray[ASCII(char)] - 1
        IF countArray[ASCII(char)] < 0:
            RETURN False
    RETURN True
'''


def test_source_c_algorithm1_ascii_is_canonicalised_to_char_conversion_with_reserved_identifier_escape():
    result = PseudocodeProfileProcessor().process(
        _source_c_algorithm1_source(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    processed = result.processed_source

    assert "ASCII" not in processed
    assert "FOR EACH __reserved_keyword__char IN str1 DO" in processed
    assert "FOR EACH __reserved_keyword__char IN str2 DO" in processed
    assert "countArray[CHAR(__reserved_keyword__char)]" in processed

    parsed = AJParserFacade().parse(processed)
    assert parsed.success, parsed.error

    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "countArray[ord(__reserved_keyword__char)]" in compiled.source_code


def test_source_c_algorithm1_compiled_behaviour_for_ascii_inputs():
    result = PseudocodeProfileProcessor().process(
        _source_c_algorithm1_source(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    python_source = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast)).source_code
    namespace = {}
    exec(python_source, namespace)
    are_anagrams = namespace["areAnagrams"]

    assert are_anagrams("listen", "silent") is True
    assert are_anagrams("aabb", "baba") is True
    assert are_anagrams("abc", "abd") is False
    assert are_anagrams("ab", "abc") is False
