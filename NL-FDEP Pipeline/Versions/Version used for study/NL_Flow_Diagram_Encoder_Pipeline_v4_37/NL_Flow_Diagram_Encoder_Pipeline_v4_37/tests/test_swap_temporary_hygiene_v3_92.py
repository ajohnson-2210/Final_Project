from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import (
    PseudocodeProfile,
    PseudocodeProfileProcessor,
    _fresh_generated_identifier,
)


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


def test_gc102_and_swap_chooses_fresh_temp_when_placeholder_is_source_state():
    source = '''FUNCTION exchange ACCEPTS(a, b)
    temp_var <- INTEGER(99)
    SWAP a AND b
    RETURN TUPLE(a, b, temp_var)
ENDFUNCTION
'''
    result = process(source)

    assert "temp_var_1 <- a" in result.processed_source
    assert "a <- b" in result.processed_source
    assert "b <- temp_var_1" in result.processed_source
    assert "temp_var <- INTEGER(99)" in result.processed_source

    compiled = compile_source(result.processed_source)
    namespace = {}
    exec(compiled, namespace)
    assert namespace["exchange"](1, 9) == (9, 1, 99)


def test_comma_swap_chooses_next_fresh_suffix_across_existing_candidates():
    source = '''FUNCTION exchange ACCEPTS(a, b)
    temp_var <- INTEGER(99)
    temp_var_1 <- INTEGER(100)
    SWAP a, b
    RETURN TUPLE(a, b, temp_var, temp_var_1)
ENDFUNCTION
'''
    result = process(source)

    assert "temp_var_2 <- a" in result.processed_source
    assert "a <- b" in result.processed_source
    assert "b <- temp_var_2" in result.processed_source
    assert "temp_var <- INTEGER(99)" in result.processed_source
    assert "temp_var_1 <- INTEGER(100)" in result.processed_source

    compiled = compile_source(result.processed_source)
    namespace = {}
    exec(compiled, namespace)
    assert namespace["exchange"](2, 7) == (7, 2, 99, 100)


def test_existing_corpus_swap_keeps_legacy_temp_var_spelling_when_available():
    source = '''FUNCTION exchange ACCEPTS(a, b)
    SWAP(a, b)
    RETURN TUPLE(a, b)
ENDFUNCTION
'''
    result = process(source)

    assert "temp_var <- a" in result.processed_source
    assert "a <- b" in result.processed_source
    assert "b <- temp_var" in result.processed_source


def test_generated_identifier_helper_never_returns_reserved_keyword():
    assert _fresh_generated_identifier("", "IF") == "IF_1"
