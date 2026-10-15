from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


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


def test_gc250_source_f_unique_set_uses_add_as_structural_set_evidence():
    source = """INPUT ipList

uniqueSet = {}

FOR ip in ipList:
    uniqueSet.add(ip)

RETURN list(uniqueSet)
"""
    result, python_source = _compile(source)
    assert "uniqueSet <- EMPTY SET" in result.processed_source
    assert "CALL add_to_set(uniqueSet, ip)" in result.processed_source
    assert any(item.rule == "GC250" for item in result.transformations)
    assert all(item.rule not in {"GC092", "GC093"} for item in result.transformations)

    namespace = {}
    exec(python_source, namespace)
    assert set(namespace["unnamed_function"](["a", "b", "a"])) == {"a", "b"}


def test_gc220_keeps_historical_id_for_indexed_write_dictionary_evidence():
    source = """INPUT s, i
seen = {}
seen[s[i]] = i
RETURN seen
"""
    result, python_source = _compile(source)
    assert "seen <- EMPTY DICTIONARY" in result.processed_source
    assert any(item.rule == "GC220" for item in result.transformations)
    assert all(item.rule not in {"GC092", "GC093"} for item in result.transformations)
    assert "seen = {}" in python_source


def test_gc250_dictionary_get_is_structural_dictionary_evidence_without_indexed_write():
    source = """INPUT key
freq = {}
value = freq.get(key, 0)
RETURN value
"""
    result, python_source = _compile(source)
    assert "freq <- EMPTY DICTIONARY" in result.processed_source
    assert any(item.rule == "GC250" for item in result.transformations)
    assert not any(item.rule == "GC220" for item in result.transformations)
    assert "freq.get(key, 0)" in python_source


def test_variable_name_alone_no_longer_classifies_empty_braces():
    for name in ("seen", "visited", "pairs", "uniqueSet", "freq", "counts", "cache", "parent"):
        result = _process(f"INPUT x\n{name} = {{}}\nRETURN {name}\n")
        assert f"{name} <- {{}}" in result.processed_source
        assert f"{name} <- EMPTY SET" not in result.processed_source
        assert f"{name} <- EMPTY DICTIONARY" not in result.processed_source
        assert all(item.rule not in {"GC092", "GC093", "GC220", "GC250"} for item in result.transformations)


def test_membership_and_iteration_are_not_enough_to_disambiguate_empty_braces():
    membership = """INPUT x
seen = {}
IF x in seen:
    RETURN TRUE
RETURN FALSE
"""
    result = _process(membership)
    assert "seen <- {}" in result.processed_source
    assert all(item.rule not in {"GC220", "GC250"} for item in result.transformations)

    iteration = """INPUT xs
values = {}
FOR EACH x IN values DO
    OUTPUT x
ENDFOR
RETURN values
"""
    result = _process(iteration)
    assert "values <- {}" in result.processed_source
    assert all(item.rule not in {"GC220", "GC250"} for item in result.transformations)


def test_conflicting_set_and_dictionary_usage_leaves_empty_braces_unresolved():
    source = """INPUT x
state = {}
state.add(x)
value = state[x]
RETURN value
"""
    result = _process(source)
    assert "state <- {}" in result.processed_source
    assert "EMPTY SET" not in result.processed_source
    assert "EMPTY DICTIONARY" not in result.processed_source
    assert all(item.rule not in {"GC220", "GC250"} for item in result.transformations)


def test_direct_rebind_stops_later_operations_from_proving_original_empty_braces():
    source = """INPUT x, other
seen = {}
seen = other
seen.add(x)
RETURN seen
"""
    result = _process(source)
    assert "seen <- {}" in result.processed_source
    assert all(item.rule not in {"GC220", "GC250"} for item in result.transformations)


def test_sibling_routine_usage_does_not_prove_another_routines_empty_braces():
    source = """FUNCTION first ACCEPTS()
    seen = {}
    RETURN seen
END FUNCTION
FUNCTION second ACCEPTS(x)
    seen.add(x)
    RETURN seen
END FUNCTION
"""
    result = _process(source)
    assert "seen <- {}" in result.processed_source
    assert all(item.rule not in {"GC220", "GC250"} for item in result.transformations)


def test_quoted_operation_text_is_not_type_evidence():
    source = '''INPUT x
seen = {}
OUTPUT "seen.add(x)"
RETURN seen
'''
    result = _process(source)
    assert "seen <- {}" in result.processed_source
    assert all(item.rule not in {"GC220", "GC250"} for item in result.transformations)
