import io
from contextlib import redirect_stdout

from aj_parser import AJParserFacade
from flow_diagram import FlowDiagramEncoder
from aj_python_compiler import AJPythonCompiler


def parse(source: str):
    return AJParserFacade().parse(source)


def compile_source(source: str) -> str:
    parsed = parse(source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success, compiled.message
    return compiled.source_code


def run_function(source: str, name: str, *args):
    python_source = compile_source(source)
    namespace = {}
    exec(python_source, namespace)
    stream = io.StringIO()
    with redirect_stdout(stream):
        result = namespace[name](*args)
    return result, stream.getvalue(), python_source


def test_exact_identifier_placeholder_is_substituted_at_output_boundary():
    result, output, python_source = run_function(
        'FUNCTION demo ACCEPTS(value)\nOUTPUT STRING("Value: {value}")\nENDFUNCTION\n',
        'demo',
        7,
    )
    assert result is None
    assert output == 'Value: 7\n'
    assert "print(f'Value: {value}')" in python_source


def test_missing_placeholder_identifier_fails_static_semantics():
    parsed = parse(
        'FUNCTION demo ACCEPTS()\nOUTPUT STRING("Value: {missing}")\nENDFUNCTION\n'
    )
    assert not parsed.success
    assert "placeholder identifier 'missing' is read before declaration or assignment" in (parsed.error or '')


def test_one_sided_assignment_does_not_make_placeholder_definitely_bound():
    parsed = parse(
        'FUNCTION demo ACCEPTS(flag)\n'
        'IF flag THEN\n'
        'value <- INTEGER(1)\n'
        'ENDIF\n'
        'OUTPUT STRING("Value: {value}")\n'
        'ENDFUNCTION\n'
    )
    assert not parsed.success
    assert "placeholder identifier 'value' is read before declaration or assignment" in (parsed.error or '')


def test_arbitrary_brace_expression_is_preserved_literal_and_never_evaluated():
    _, output, python_source = run_function(
        'FUNCTION demo ACCEPTS()\nOUTPUT STRING("Value: {1+2}")\nENDFUNCTION\n',
        'demo',
    )
    assert output == 'Value: {1+2}\n'
    assert "print('Value: {1+2}')" in python_source
    assert 'f' not in python_source.split('print(', 1)[1].split(')', 1)[0][:1]


def test_format_spec_and_conversion_like_braces_remain_literal_text():
    _, output, _ = run_function(
        'FUNCTION demo ACCEPTS(value)\n'
        'OUTPUT STRING("{value!r} {value:>4} {value}")\n'
        'ENDFUNCTION\n',
        'demo',
        3,
    )
    assert output == '{value!r} {value:>4} 3\n'


def test_double_braces_do_not_become_placeholder_escape_syntax():
    _, output, _ = run_function(
        'FUNCTION demo ACCEPTS(value)\nOUTPUT STRING("{{value}} / {value}")\nENDFUNCTION\n',
        'demo',
        9,
    )
    assert output == '{{value}} / 9\n'


def test_non_output_string_literal_keeps_braces_as_plain_string_data():
    python_source = compile_source(
        'FUNCTION demo ACCEPTS()\n'
        'value <- STRING("{1+2} {missing}")\n'
        'RETURN value\n'
        'ENDFUNCTION\n'
    )
    namespace = {}
    exec(python_source, namespace)
    assert namespace['demo']() == '{1+2} {missing}'
