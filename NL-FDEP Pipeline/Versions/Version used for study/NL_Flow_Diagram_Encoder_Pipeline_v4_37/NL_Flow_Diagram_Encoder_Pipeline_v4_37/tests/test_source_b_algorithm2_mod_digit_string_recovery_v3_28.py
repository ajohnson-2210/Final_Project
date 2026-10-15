import pytest

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
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    return compiled.source_code


def test_source_b_algorithm2_exact_source_preserves_mixed_numeric_string_addition():
    source = '''FUNCTION decimalToBinary(n):
    IF n == 0 THEN RETURN "0"
    result ← ""
    WHILE n > 0:
        result ← (n MOD 2) + result
        n ← n DIV 2
    RETURN result
'''
    result = process(source)

    assert "result <- (n MODULUS 2) + result" in result.processed_source
    assert "CALL to_string((n MODULUS 2))" not in result.processed_source
    assert not any(t.rule == "GC230" for t in result.transformations)

    compiled = compile_source(result.processed_source)
    assert "result = ((n % 2) + result)" in compiled

    namespace = {}
    exec(compiled, namespace)
    decimal_to_binary = namespace["decimalToBinary"]
    assert decimal_to_binary(0) == "0"
    with pytest.raises(TypeError, match="int.*str"):
        decimal_to_binary(5)


def test_source_b_algorithm2_audit_counterfactual_explicit_string_conversion_makes_algorithm_viable():
    """Audit-only diagnosis: do not apply this replacement in production."""
    source = '''FUNCTION decimalToBinary(n):
    IF n == 0 THEN RETURN "0"
    result ← ""
    WHILE n > 0:
        result ← (n MOD 2) + result
        n ← n DIV 2
    RETURN result
'''
    result = process(source)
    compiled = compile_source(result.processed_source)

    repaired_for_audit = compiled.replace(
        "result = ((n % 2) + result)",
        "result = (str((n % 2)) + result)",
    )
    assert repaired_for_audit != compiled

    namespace = {}
    exec(repaired_for_audit, namespace)
    decimal_to_binary = namespace["decimalToBinary"]
    for value in range(0, 4097):
        assert decimal_to_binary(value) == bin(value)[2:]


def test_gc230_is_retired_for_already_canonical_modulus_spelling_too():
    source = '''FUNCTION build ACCEPTS(n)
    text <- EMPTY STRING
    text <- (n MODULUS 2) + text
    RETURN text
ENDFUNCTION
'''
    result = process(source)
    assert "text <- (n MODULUS 2) + text" in result.processed_source
    assert "CALL to_string" not in result.processed_source
    assert not any(t.rule == "GC230" for t in result.transformations)


def test_no_implicit_coercion_without_explicit_string_backing():
    source = '''FUNCTION build ACCEPTS(n)
    text <- INTEGER(0)
    text <- (n MOD 2) + text
    RETURN text
ENDFUNCTION
'''
    result = process(source)
    assert "CALL to_string" not in result.processed_source


def test_explicit_string_conversion_remains_supported():
    source = '''FUNCTION decimalToBinary(n):
    IF n == 0:
        RETURN "0"
    binaryString = ""
    WHILE n > 0:
        remainder = n MOD 2
        binaryString = STRING(remainder) + binaryString
        n = n DIV 2
    RETURN binaryString
'''
    result = process(source)

    assert "binaryString <- CALL to_string(remainder) + binaryString" in result.processed_source
    assert any(t.rule == "GC225" for t in result.transformations)

    compiled = compile_source(result.processed_source)
    assert "str(remainder)" in compiled
    namespace = {}
    exec(compiled, namespace)
    fn = namespace["decimalToBinary"]
    for value in range(0, 257):
        assert fn(value) == bin(value)[2:]
