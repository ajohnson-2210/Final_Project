from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_f_ALGORITHM_25 = """INPUT s

maxLen = 0
start = 0
seen = {}

FOR i from 0 to length(s)-1:
    IF s[i] in seen AND seen[s[i]] >= start:
        start = seen[s[i]] + 1

    seen[s[i]] = i
    maxLen = MAX(maxLen, i - start + 1)

RETURN maxLen
"""


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )


def _compile(source: str):
    result = _process(source)
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    return result, compiled.source_code


def test_source_f25_nested_index_write_proves_empty_braces_are_dictionary():
    result, python_source = _compile(source_f_ALGORITHM_25)
    assert "seen <- EMPTY DICTIONARY" in result.processed_source
    assert any(item.rule == "GC220" for item in result.transformations)
    assert "seen = {}" in python_source
    assert "seen[s[i]] = i" in python_source

    namespace = {}
    exec(python_source, namespace)
    fn = namespace["unnamed_function"]
    assert fn("") == 0
    assert fn("abcabcbb") == 3
    assert fn("bbbbb") == 1
    assert fn("pwwkew") == 3
    assert fn("abba") == 2


def test_gc220_accepts_deeper_balanced_nested_index_expression():
    source = """INPUT xs, i, j
seen = {}
seen[xs[i[j]]] = 1
RETURN seen
"""
    result = _process(source)
    assert "seen <- EMPTY DICTIONARY" in result.processed_source
    assert any(item.rule == "GC220" for item in result.transformations)


def test_gc220_refuses_nested_index_comparison_only():
    source = """INPUT s, i
seen = {}
IF seen[s[i]] == 1:
    RETURN TRUE
RETURN FALSE
"""
    result = _process(source)
    assert not any(item.rule == "GC220" for item in result.transformations)


def test_gc220_refuses_nested_index_read_only():
    source = """INPUT s, i
seen = {}
value = seen[s[i]]
RETURN value
"""
    result = _process(source)
    assert not any(item.rule == "GC220" for item in result.transformations)


def test_gc220_refuses_other_receiver_nested_index_write():
    source = """INPUT s, i
seen = {}
other[s[i]] = 1
RETURN seen
"""
    result = _process(source)
    assert not any(item.rule == "GC220" for item in result.transformations)
