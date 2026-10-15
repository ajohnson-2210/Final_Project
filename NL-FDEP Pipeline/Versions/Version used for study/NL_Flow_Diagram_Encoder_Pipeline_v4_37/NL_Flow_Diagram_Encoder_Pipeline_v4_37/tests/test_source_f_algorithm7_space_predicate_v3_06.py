from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


# Exact motivating source_f Algorithm 7 occurrence retained as audit evidence.
SOURCE = '''INPUT sentence

words = []
current = ""

FOR each char in sentence:
    IF char is space:
        IF current != "":
            words.append(current)
            current = ""
    ELSE:
        current += char

IF current != "":
    words.append(current)

RETURN words
'''


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def test_source_f_algorithm7_exact_space_predicate_recovers_without_broadening():
    result = _process(SOURCE)

    assert 'IF __reserved_keyword__char == CHAR(" ") THEN' in result.processed_source
    assert 'is space' not in result.processed_source.lower()
    assert 'is_whitespace' not in result.processed_source.lower()
    assert sum(item.rule == 'GC207' for item in result.transformations) == 1

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    assert "if (__reserved_keyword__char == ' '):" in compiled.source_code

    namespace = {}
    exec(compiled.source_code, namespace)
    assert namespace['unnamed_function']('one two  three') == ['one', 'two', 'three']
    assert namespace['unnamed_function']('') == []
    assert namespace['unnamed_function']('  ') == []
