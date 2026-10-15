from pseudocode_profiles import GenericPseudocodeProcessor
from aj_parser import AJParserFacade
from flow_diagram import FlowDiagramEncoder
from aj_python_compiler import AJPythonCompiler


source_e_8 = '''FUNCTION SORT_WORDS(words)
  RETURN SORT(words, ALPHABETICAL_ORDER)
END FUNCTION
'''


def _compile(source=source_e_8):
    result = GenericPseudocodeProcessor().process(source)
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    flow = FlowDiagramEncoder().encode(parsed.ast)
    compiled = AJPythonCompiler().compile(flow)
    namespace = {}
    exec(compiled.source_code, namespace)
    return result, compiled.source_code, namespace


def test_gc228_recovers_exact_source_e8_alphabetical_sort_mode():
    result, python_source, namespace = _compile()
    gc228 = [t for t in result.transformations if t.rule == 'GC228']
    assert len(gc228) == 1
    assert 'RETURN CALL sort_value(words)' in result.processed_source
    assert 'return sorted(words)' in python_source
    fn = namespace['SORT_WORDS']
    assert fn(['hello', 'world', 'abc', 'xyz']) == ['abc', 'hello', 'world', 'xyz']
    assert fn(['b', 'A', 'aa', 'a']) == sorted(['b', 'A', 'aa', 'a'])
    assert fn([]) == []


def test_gc228_does_not_reinterpret_arbitrary_sort_comparator():
    source = '''FUNCTION f(words, comparator)
  RETURN SORT(words, comparator)
END FUNCTION
'''
    result = GenericPseudocodeProcessor().process(source)
    assert not any(t.rule == 'GC228' for t in result.transformations)
    assert 'SORT(words, comparator)' in result.processed_source


def test_gc228_does_not_reinterpret_descending_marker():
    source = '''FUNCTION f(words)
  RETURN SORT(words, DESCENDING_ORDER)
END FUNCTION
'''
    result = GenericPseudocodeProcessor().process(source)
    assert not any(t.rule == 'GC228' for t in result.transformations)
    assert 'DESCENDING_ORDER' in result.processed_source


def test_gc228_does_not_reinterpret_member_sort_call():
    source = '''FUNCTION f(words)
  RETURN helper.SORT(words, ALPHABETICAL_ORDER)
END FUNCTION
'''
    result = GenericPseudocodeProcessor().process(source)
    assert not any(t.rule == 'GC228' for t in result.transformations)
    assert 'sort_value' not in result.processed_source


def test_gc228_requires_two_arguments():
    source = '''FUNCTION f(words)
  RETURN SORT(words)
END FUNCTION
'''
    result = GenericPseudocodeProcessor().process(source)
    assert not any(t.rule == 'GC228' for t in result.transformations)
