from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


SOURCE = '''FUNCTION decimalToBinary(n):
    IF n == 0:
        RETURN "0"
    binaryString = ""
    WHILE n > 0:
        remainder = n MOD 2
        binaryString = STRING(remainder) + binaryString
        n = n DIV 2
    RETURN binaryString
'''


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def test_source_c_algorithm2_exact_source_uses_evidenced_numeric_string_conversion():
    result = _process(SOURCE)
    assert "binaryString <- CALL to_string(remainder) + binaryString" in result.processed_source
    gc225 = [item for item in result.transformations if item.rule == "GC225"]
    assert gc225

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "binaryString = (str(remainder) + binaryString)" in compiled.source_code

    namespace = {}
    exec(compiled.source_code, namespace)
    fn = namespace["decimalToBinary"]
    for n in range(0, 2049):
        assert fn(n) == bin(n)[2:]


def test_gc225_is_identifier_agnostic_when_evidence_is_equivalent():
    source = '''FUNCTION Convert ACCEPTS(value)
    text <- EMPTY STRING
    digit <- value MODULUS 2
    text <- STRING(digit) + text
    RETURN text
ENDFUNCTION
'''
    result = _process(source)
    assert "text <- CALL to_string(digit) + text" in result.processed_source
    assert any(item.rule == "GC225" for item in result.transformations)


def test_gc225_does_not_reinterpret_ordinary_string_literals():
    source = '''FUNCTION Example ACCEPTS(value)
    text <- EMPTY STRING
    digit <- value MODULUS 2
    text <- STRING("digit") + text
    RETURN text
ENDFUNCTION
'''
    result = _process(source)
    assert 'text <- STRING("digit") + text' in result.processed_source
    assert not any(item.rule == "GC225" for item in result.transformations)


def test_gc225_requires_numeric_evidence_for_converted_identifier():
    source = '''FUNCTION Example ACCEPTS(value)
    text <- EMPTY STRING
    digit <- value
    text <- STRING(digit) + text
    RETURN text
ENDFUNCTION
'''
    result = _process(source)
    assert "text <- STRING(digit) + text" in result.processed_source
    assert not any(item.rule == "GC225" for item in result.transformations)


def test_gc225_requires_string_backed_destination():
    source = '''FUNCTION Example ACCEPTS(value)
    text <- 0
    digit <- value MODULUS 2
    text <- STRING(digit) + text
    RETURN text
ENDFUNCTION
'''
    result = _process(source)
    assert "text <- STRING(digit) + text" in result.processed_source
    assert not any(item.rule == "GC225" for item in result.transformations)


def test_gc225_does_not_convert_unrelated_string_calls():
    source = '''FUNCTION Example ACCEPTS(value)
    digit <- value MODULUS 2
    RETURN STRING(digit)
ENDFUNCTION
'''
    result = _process(source)
    assert "RETURN STRING(digit)" in result.processed_source
    assert not any(item.rule == "GC225" for item in result.transformations)
