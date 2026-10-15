from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _process_and_compile(source: str):
    result = PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    return result, compiled.source_code


def test_bare_comma_output_is_multiple_print_arguments_not_tuple_data():
    result, python_source = _process_and_compile(
        '''FUNCTION pair ACCEPTS(a, b)\n    OUTPUT a, b\nENDFUNCTION\n'''
    )
    assert 'OUTPUT CALL output_values(a, b)' in result.processed_source
    assert 'OUTPUT TUPLE(a, b)' not in result.processed_source
    assert 'print(a, b)' in python_source
    assert 'print((a, b))' not in python_source


def test_parenthesised_output_tuple_remains_tuple_data():
    result, python_source = _process_and_compile(
        '''FUNCTION pair ACCEPTS(a, b)\n    OUTPUT (a, b)\nENDFUNCTION\n'''
    )
    assert 'OUTPUT TUPLE(a, b)' in result.processed_source
    assert 'OUTPUT CALL output_values' not in result.processed_source
    assert 'print((a, b))' in python_source


def test_explicit_tuple_output_remains_tuple_data():
    result, python_source = _process_and_compile(
        '''FUNCTION pair ACCEPTS(a, b)\n    OUTPUT TUPLE(a, b)\nENDFUNCTION\n'''
    )
    assert 'OUTPUT TUPLE(a, b)' in result.processed_source
    assert 'OUTPUT CALL output_values' not in result.processed_source
    assert 'print((a, b))' in python_source


def test_multiple_output_arguments_can_contain_index_expressions():
    result, python_source = _process_and_compile(
        '''FUNCTION pair ACCEPTS(Array, i, j)\n    OUTPUT Array[i], Array[j]\nENDFUNCTION\n'''
    )
    assert 'OUTPUT CALL output_values(Array[i], Array[j])' in result.processed_source
    assert 'print(Array[i], Array[j])' in python_source
