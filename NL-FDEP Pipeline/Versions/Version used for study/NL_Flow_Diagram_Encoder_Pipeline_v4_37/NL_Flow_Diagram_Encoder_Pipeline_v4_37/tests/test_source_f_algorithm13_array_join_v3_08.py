from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


SOURCE = '''INPUT s

chars = array(s)
left = 0
right = length(s)-1

WHILE left < right:
    swap(chars[left], chars[right])
    left++
    right--

RETURN join(chars)
'''


def test_source_f_algorithm13_uses_list_conversion_and_empty_separator_join():
    result = PseudocodeProfileProcessor().process(
        SOURCE, PseudocodeProfile.GENERIC_COMPATIBILITY
    )

    assert 'chars <- CALL to_array(s)' in result.processed_source
    assert 'RETURN JOIN(chars, EMPTY STRING)' in result.processed_source
    assert 'CALL array(' not in result.processed_source
    assert [t.rule for t in result.transformations].count('GC209') == 1
    assert [t.rule for t in result.transformations].count('GC210') == 1

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert 'chars = list(s)' in compiled.source_code
    assert "return ''.join(chars)" in compiled.source_code

    namespace = {}
    exec(compiled.source_code, namespace)
    assert namespace['unnamed_function']('hello') == 'olleh'
    assert namespace['unnamed_function']('') == ''
    assert namespace['unnamed_function']('a') == 'a'
