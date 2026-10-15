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


def test_source_c_algorithm19_preserves_lowercase_swap_function_identifier():
    source = '''FUNCTION swap(a, b):
    a = a + b
    b = a - b
    a = a - b
    RETURN (a, b)
'''
    result = process(source)

    assert "FUNCTION swap ACCEPTS(a, b)" in result.processed_source
    assert "FUNCTION SWAP ACCEPTS(a, b)" not in result.processed_source
    assert all(t.rule != "GC051" for t in result.transformations)

    compiled = compile_source(result.processed_source)
    assert "def swap(a, b):" in compiled
    assert "def SWAP(a, b):" not in compiled

    namespace = {}
    exec(compiled, namespace)
    assert namespace["swap"](7, 3) == (3, 7)
    assert namespace["swap"](-5, 8) == (8, -5)


def test_gc051_still_normalises_standalone_swap_call():
    source = '''FUNCTION exchange ACCEPTS(a, b)
    SWAP(a, b)
    RETURN TUPLE(a, b)
ENDFUNCTION
'''
    result = process(source)

    assert any(t.rule == "GC051" for t in result.transformations)
    # Later compatibility passes lower the canonical SWAP statement to its
    # existing temporary-variable implementation.
    assert "temp_var <- a" in result.processed_source
    assert "a <- b" in result.processed_source
    assert "b <- temp_var" in result.processed_source

    compiled = compile_source(result.processed_source)
    namespace = {}
    exec(compiled, namespace)
    assert namespace["exchange"](1, 9) == (9, 1)


def test_gc051_does_not_rewrite_swap_inside_assignment_expression():
    source = '''FUNCTION keep ACCEPTS(a, b)
    result <- CALL swap(a, b)
    RETURN result
ENDFUNCTION
'''
    result = process(source)
    assert "CALL swap(a, b)" in result.processed_source
    assert all(t.rule != "GC051" for t in result.transformations)


def test_gc051_does_not_rewrite_member_method_named_swap():
    source = '''FUNCTION keep ACCEPTS(obj, a, b)
    CALL obj.swap(a, b)
    RETURN obj
ENDFUNCTION
'''
    result = process(source)
    assert "obj.swap(a, b)" in result.processed_source
    assert all(t.rule != "GC051" for t in result.transformations)
