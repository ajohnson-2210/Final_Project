from pseudocode_profiles import GenericPseudocodeProcessor
from aj_parser import AJParserFacade
from flow_diagram import FlowDiagramEncoder
from aj_python_compiler import AJPythonCompiler


source_e_5 = r'''FUNCTION REMOVE_PUNCTUATION(sentence)
  RETURN REPLACE_ALL(sentence, "[^a-zA-Z0-9\s]", "")
END FUNCTION
'''


def _compile(source=source_e_5):
    result = GenericPseudocodeProcessor().process(source)
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    flow = FlowDiagramEncoder().encode(parsed.ast)
    compiled = AJPythonCompiler().compile(flow)
    namespace = {}
    exec(compiled.source_code, namespace)
    return result, compiled.source_code, namespace


def test_gc227_recovers_exact_source_e5_regex_replace_all_and_preserves_backslash_escape():
    result, python_source, namespace = _compile()
    gc227 = [t for t in result.transformations if t.rule == "GC227"]
    assert len(gc227) == 1
    assert 'RETURN CALL regex_replace(sentence, STRING("[^a-zA-Z0-9\\\\s]"), EMPTY STRING)' in result.processed_source
    assert "__import__('re').sub('[^a-zA-Z0-9\\\\s]', '', sentence)" in python_source
    fn = namespace['REMOVE_PUNCTUATION']
    assert fn('Hello, world!') == 'Hello world'
    assert fn('A\tB\nC!') == 'A\tB\nC'
    assert fn('abc_123-!?') == 'abc123'


def test_gc227_preserves_regex_replacement_backreferences_across_aj_string_lexing():
    source = r'''FUNCTION double_letters(text)
  RETURN REPLACE_ALL(text, "([a-z])", "\1\1")
END FUNCTION
'''
    result, _, namespace = _compile(source)
    assert any(t.rule == 'GC227' for t in result.transformations)
    assert namespace['double_letters']('ab') == 'aabb'


def test_gc227_does_not_reinterpret_plain_literal_replace_all_without_regex_evidence():
    source = '''FUNCTION f(text)
  RETURN REPLACE_ALL(text, "a", "b")
END FUNCTION
'''
    result = GenericPseudocodeProcessor().process(source)
    assert not any(t.rule == 'GC227' for t in result.transformations)
    assert 'REPLACE_ALL' in result.processed_source
    assert 'regex_replace' not in result.processed_source


def test_gc227_does_not_reinterpret_member_replace_all():
    source = r'''FUNCTION f(text)
  RETURN text.REPLACE_ALL("[^a]", "")
END FUNCTION
'''
    result = GenericPseudocodeProcessor().process(source)
    assert not any(t.rule == 'GC227' for t in result.transformations)
    assert 'regex_replace' not in result.processed_source


def test_gc227_requires_exactly_three_arguments():
    source = r'''FUNCTION f(text)
  RETURN REPLACE_ALL(text, "[^a]")
END FUNCTION
'''
    result = GenericPseudocodeProcessor().process(source)
    assert not any(t.rule == 'GC227' for t in result.transformations)
    assert 'regex_replace' not in result.processed_source
