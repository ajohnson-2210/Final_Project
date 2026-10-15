from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_f_ALGORITHM_34 = '''INPUT list1, list2

set1 = set(list1)
result = []

FOR item in list2:
    IF item in set1 AND item not in result:
        result.append(item)

RETURN unique(result)
'''


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def _compile(processed_source: str) -> str:
    parsed = AJParserFacade().parse(processed_source)
    assert parsed.success, parsed.error
    return AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast)).source_code


def test_source_f34_unique_return_keeps_set_semantics_even_when_values_are_already_unique():
    result = _process(source_f_ALGORITHM_34)

    assert "RETURN CALL to_set(result)" in result.processed_source
    assert not any(item.rule == "GC214" for item in result.transformations)
    assert any(item.rule == "GC222" for item in result.transformations)

    python_source = _compile(result.processed_source)
    namespace = {}
    exec(python_source, namespace)
    actual = namespace["unnamed_function"](
        [1, 2, 2, 3, 5],
        [2, 2, 4, 3, 2, 1, 1, 5, 3],
    )
    assert actual == {1, 2, 3, 5}
    assert isinstance(actual, set)


def test_gc214_is_retired_because_value_uniqueness_does_not_make_set_conversion_redundant():
    result = _process(source_f_ALGORITHM_34)
    assert not any(item.rule == "GC214" for item in result.transformations)
    entries = [
        item for item in result.to_dict()["transformations"]
        if item["branch"] == "EXACT_UNIQUE_TO_SET_INTRINSIC"
    ]
    assert len(entries) == 1
    assert entries[0]["rule_family"] == "COLLECTION_DEDUPLICATION"
    assert entries[0]["confidence"] == "user_confirmed"
    assert entries[0]["semantic_change"] is False

def test_gc214_refuses_unguarded_append():
    source = '''INPUT items
result = []
FOR EACH item IN items DO
    APPEND item TO result
ENDFOR
RETURN unique(result)
'''
    result = _process(source)
    assert "RETURN CALL to_set(result)" in result.processed_source
    assert not any(item.rule == "GC214" for item in result.transformations)
    assert any(item.rule == "GC222" for item in result.transformations)


def test_gc214_refuses_mismatched_nonmembership_guard():
    source = '''INPUT items
result = []
FOR EACH item IN items DO
    IF item NOT IN result THEN
        APPEND CALL transform(item) TO result
    ENDIF
ENDFOR
RETURN unique(result)
'''
    result = _process(source)
    assert "RETURN CALL to_set(result)" in result.processed_source
    assert not any(item.rule == "GC214" for item in result.transformations)
    assert any(item.rule == "GC222" for item in result.transformations)


def test_gc214_refuses_append_in_else_branch_of_nonmembership_test():
    source = '''INPUT items
result = []
FOR EACH item IN items DO
    IF item NOT IN result THEN
        OUTPUT item
    ELSE
        APPEND item TO result
    ENDIF
ENDFOR
RETURN unique(result)
'''
    result = _process(source)
    assert "RETURN CALL to_set(result)" in result.processed_source
    assert not any(item.rule == "GC214" for item in result.transformations)
    assert any(item.rule == "GC222" for item in result.transformations)


def test_gc214_refuses_reassignment_after_empty_list_initialisation():
    source = '''INPUT items
result = []
result <- CALL prepare(items)
IF item NOT IN result THEN
    APPEND item TO result
ENDIF
RETURN unique(result)
'''
    result = _process(source)
    assert "RETURN CALL to_set(result)" in result.processed_source
    assert not any(item.rule == "GC214" for item in result.transformations)
    assert any(item.rule == "GC222" for item in result.transformations)


def test_gc214_refuses_indexed_write_even_when_append_is_guarded():
    source = '''INPUT items
result = []
FOR EACH item IN items DO
    IF item NOT IN result THEN
        APPEND item TO result
    ENDIF
ENDFOR
result[0] <- items[0]
RETURN unique(result)
'''
    result = _process(source)
    assert "RETURN CALL to_set(result)" in result.processed_source
    assert not any(item.rule == "GC214" for item in result.transformations)
    assert any(item.rule == "GC222" for item in result.transformations)


def test_gc214_is_not_a_global_unique_identity_rewrite():
    source = '''INPUT items
RETURN unique(items)
'''
    result = _process(source)
    assert "RETURN CALL to_set(items)" in result.processed_source
    assert not any(item.rule == "GC214" for item in result.transformations)
    assert any(item.rule == "GC222" for item in result.transformations)


def test_gc214_refuses_two_appends_under_one_nonmembership_guard():
    source = '''INPUT item
result = []
IF item NOT IN result THEN
    APPEND item TO result
    APPEND item TO result
ENDIF
RETURN unique(result)
'''
    result = _process(source)
    assert "RETURN CALL to_set(result)" in result.processed_source
    assert not any(item.rule == "GC214" for item in result.transformations)
    assert any(item.rule == "GC222" for item in result.transformations)


def test_gc214_refuses_guard_outside_repeating_loop():
    source = '''INPUT item, count
result = []
IF item NOT IN result THEN
    FOR i FROM 0 TO count - 1 DO
        APPEND item TO result
    ENDFOR
ENDIF
RETURN unique(result)
'''
    result = _process(source)
    assert "RETURN CALL to_set(result)" in result.processed_source
    assert not any(item.rule == "GC214" for item in result.transformations)
    assert any(item.rule == "GC222" for item in result.transformations)


def test_gc214_refuses_alias_escape():
    source = '''INPUT items
result = []
alias <- result
FOR EACH item IN items DO
    IF item NOT IN result THEN
        APPEND item TO result
    ENDIF
ENDFOR
RETURN unique(result)
'''
    result = _process(source)
    assert "RETURN CALL to_set(result)" in result.processed_source
    assert not any(item.rule == "GC214" for item in result.transformations)
    assert any(item.rule == "GC222" for item in result.transformations)


def test_gc214_refuses_unknown_call_escape():
    source = '''INPUT items
result = []
FOR EACH item IN items DO
    IF item NOT IN result THEN
        APPEND item TO result
    ENDIF
ENDFOR
CALL inspect(result)
RETURN unique(result)
'''
    result = _process(source)
    assert "RETURN CALL to_set(result)" in result.processed_source
    assert not any(item.rule == "GC214" for item in result.transformations)
    assert any(item.rule == "GC222" for item in result.transformations)
