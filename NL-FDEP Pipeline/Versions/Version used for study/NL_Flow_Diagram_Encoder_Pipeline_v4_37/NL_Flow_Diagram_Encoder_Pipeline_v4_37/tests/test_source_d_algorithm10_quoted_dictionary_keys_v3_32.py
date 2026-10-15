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


def test_source_d_algorithm10_quoted_vowel_dictionary_keys_execute():
    source = '''FUNCTION CountVowels(text):
    vowel_counts = {'a': 0, 'e': 0, 'i': 0, 'o': 0, 'u': 0}

    FOR EACH char IN lowercase(text) DO
        IF char IN vowel_counts THEN
            vowel_counts[char] = vowel_counts[char] + 1
        END IF
    END FOR

    RETURN vowel_counts
END FUNCTION
'''
    result = process(source)

    assert any(t.rule == "GC097" for t in result.transformations)
    for vowel in "aeiou":
        assert f'vowel_counts[STRING("{vowel}")] <- 0' in result.processed_source

    compiled = compile_source(result.processed_source)
    namespace = {}
    exec(compiled, namespace)
    assert namespace["CountVowels"]("Abracadabra EEL") == {
        "a": 5,
        "e": 2,
        "i": 0,
        "o": 0,
        "u": 0,
    }


def test_gc097_preserves_existing_bare_key_stringification():
    source = '''FUNCTION f ACCEPTS()
    values <- {a: 1, b: 2}
    RETURN values
ENDFUNCTION
'''
    result = process(source)
    assert 'values[STRING("a")] <- 1' in result.processed_source
    assert 'values[STRING("b")] <- 2' in result.processed_source
    compile_source(result.processed_source)


def test_gc097_renders_single_and_double_quoted_string_keys_canonically():
    source = '''FUNCTION f ACCEPTS()
    values <- {'left': 1, "right": 2}
    RETURN values
ENDFUNCTION
'''
    result = process(source)
    assert 'values[STRING("left")] <- 1' in result.processed_source
    assert 'values[STRING("right")] <- 2' in result.processed_source
    compiled = compile_source(result.processed_source)
    namespace = {}
    exec(compiled, namespace)
    assert namespace["f"]() == {"left": 1, "right": 2}


def test_gc097_preserves_escaped_quote_in_quoted_string_key():
    source = '''FUNCTION f ACCEPTS()
    values <- {"a\\\"b": 1}
    RETURN values
ENDFUNCTION
'''
    result = process(source)
    assert 'values[STRING("a\\\"b")] <- 1' in result.processed_source
    compiled = compile_source(result.processed_source)
    namespace = {}
    exec(compiled, namespace)
    assert namespace["f"]() == {'a"b': 1}
