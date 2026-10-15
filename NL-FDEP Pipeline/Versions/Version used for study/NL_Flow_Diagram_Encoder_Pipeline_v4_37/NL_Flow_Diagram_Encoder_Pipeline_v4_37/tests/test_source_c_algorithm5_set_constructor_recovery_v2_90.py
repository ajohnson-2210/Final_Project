from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_c_ALGORITHM_5 = r'''FUNCTION removePunctuation(sentence):
    punctuation = set(". , ! ? ; : ' \" - ( ) [ ] { }")
    result = ""
    FOR each char in sentence:
        IF char NOT IN punctuation:
            result = result + char
    RETURN result
'''


def test_source_c_algorithm5_uses_general_set_constructor_recovery():
    result = PseudocodeProfileProcessor().process(
        source_c_ALGORITHM_5,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )

    assert "punctuation <- CALL to_set(" in result.processed_source
    assert "CALL set(" not in result.processed_source
    assert "FOR EACH __reserved_keyword__char IN sentence DO" in result.processed_source

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "punctuation = set(" in compiled.source_code

    namespace = {}
    exec(compiled.source_code, namespace)
    # Preserve the source exactly: its set literal includes a space, so spaces
    # are removed along with punctuation rather than silently repairing it.
    assert namespace["removePunctuation"]("Hello, World!") == "HelloWorld"
