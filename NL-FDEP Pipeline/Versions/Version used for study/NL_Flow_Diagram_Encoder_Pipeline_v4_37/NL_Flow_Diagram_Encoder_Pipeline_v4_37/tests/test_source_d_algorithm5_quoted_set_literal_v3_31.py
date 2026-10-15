from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def compile_source(processed_source: str) -> str:
    parsed = AJParserFacade().parse(processed_source)
    assert parsed.success, parsed.error
    return AJPythonCompiler().compile(
        FlowDiagramEncoder().encode(parsed.ast)
    ).source_code


def test_source_d_algorithm5_quoted_punctuation_set_executes_with_quotes_preserved():
    source = '''FUNCTION RemovePunctuation(sentence):
    punctuation_set = {'.', ',', '!', '?', ';', ':', '-', '\\'', '"', '(', ')'}
    clean_sentence = ""
    FOR EACH char IN sentence DO
        IF char NOT IN punctuation_set THEN
            clean_sentence = clean_sentence + char
        END IF
    END FOR
    RETURN clean_sentence
END FUNCTION
'''
    result = process(source)

    assert any(t.rule == "GC231" for t in result.transformations)
    assert (
        'punctuation_set <- CALL to_set(CALL list_value('
        'STRING("."), STRING(","), STRING("!"), STRING("?"), STRING(";"), '
        'STRING(":"), STRING("-"), STRING("\'"), STRING("\\\""), '
        'STRING("("), STRING(")")))'
        in result.processed_source
    )

    compiled = compile_source(result.processed_source)
    assert "punctuation_set = set([" in compiled
    assert '''"'"''' in compiled
    assert ''''"' '''.strip() in compiled

    namespace = {}
    exec(compiled, namespace)
    remove_punctuation = namespace["RemovePunctuation"]
    assert remove_punctuation("Hello, world!") == "Hello world"
    assert remove_punctuation('a\'b"c(d)-e?') == "abcde"
    assert remove_punctuation("plain text") == "plain text"


def test_gc231_accepts_only_nonempty_quoted_scalar_set_assignment():
    result = process('''FUNCTION f ACCEPTS()
    values <- {"a", 'b', "c"}
    RETURN values
ENDFUNCTION
''')
    assert any(t.rule == "GC231" for t in result.transformations)
    assert (
        'values <- CALL to_set(CALL list_value(STRING("a"), STRING("b"), STRING("c")))'
        in result.processed_source
    )
    compile_source(result.processed_source)


def test_gc231_does_not_claim_dictionary_literal():
    result = process('''FUNCTION f ACCEPTS()
    values <- {"a": 1, "b": 2}
    RETURN values
ENDFUNCTION
''')
    assert all(t.rule != "GC231" for t in result.transformations)


def test_gc231_does_not_claim_empty_braces():
    result = process('''FUNCTION f ACCEPTS()
    values <- {}
    RETURN values
ENDFUNCTION
''')
    assert all(t.rule != "GC231" for t in result.transformations)


def test_gc231_does_not_claim_mixed_or_unquoted_set_members():
    for literal in ('{"a", value}', '{"a", 1}', '{value, other}'):
        result = process(f'''FUNCTION f ACCEPTS(value, other)
    values <- {literal}
    RETURN values
ENDFUNCTION
''')
        assert all(t.rule != "GC231" for t in result.transformations), literal


def test_gc231_does_not_claim_set_comprehension():
    result = process('''FUNCTION f ACCEPTS(items)
    values <- {x for x in items}
    RETURN values
ENDFUNCTION
''')
    assert all(t.rule != "GC231" for t in result.transformations)


def test_gc231_refuses_unrepresentable_control_character_scalar():
    source = "FUNCTION f ACCEPTS()\n    values <- {'\\x01'}\n    RETURN values\nENDFUNCTION\n"
    result = process(source)
    assert all(t.rule != "GC231" for t in result.transformations)
