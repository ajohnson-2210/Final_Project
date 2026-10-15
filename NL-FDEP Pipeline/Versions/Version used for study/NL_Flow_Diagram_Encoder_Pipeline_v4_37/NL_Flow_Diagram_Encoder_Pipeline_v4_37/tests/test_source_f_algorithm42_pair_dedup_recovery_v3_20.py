from itertools import product

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_f_ALGORITHM_42 = """INPUT arr, target

seen = {}
pairs = []

FOR num in arr:
    comp = target - num

    IF comp in seen:
        pairs.add((MIN(num, comp), MAX(num, comp)))

    seen[num] = true

RETURN unique(pairs)
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


def test_source_f42_exact_source_recovers_dictionary_list_add_tuple_and_unique():
    result, python_source = _compile(source_f_ALGORITHM_42)

    canonical = result.processed_source
    assert "seen <- EMPTY DICTIONARY" in canonical
    assert "pairs <- EMPTY LIST" in canonical
    assert "APPEND TUPLE(CALL min(num, comp), CALL max(num, comp)) TO pairs" in canonical
    assert "RETURN CALL to_set(pairs)" in canonical

    rules = [item.rule for item in result.transformations]
    assert "GC220" in rules
    assert "GC221" in rules
    assert "GC222" in rules

    assert "seen = {}" in python_source
    assert "pairs = []" in python_source
    assert "pairs.append((min(num, comp), max(num, comp)))" in python_source
    assert "return set(pairs)" in python_source


def test_source_f42_generated_python_matches_unique_value_pair_reference_exhaustively():
    _, python_source = _compile(source_f_ALGORITHM_42)
    namespace = {}
    exec(python_source, namespace)
    fn = namespace["unnamed_function"]

    values = (-2, -1, 0, 1, 2)
    targets = range(-4, 5)

    def reference(arr, target):
        found = set()
        for i in range(len(arr)):
            for j in range(i + 1, len(arr)):
                if arr[i] + arr[j] == target:
                    found.add((min(arr[i], arr[j]), max(arr[i], arr[j])))
        return found

    for length in range(0, 6):
        for arr in product(values, repeat=length):
            for target in targets:
                assert fn(list(arr), target) == reference(arr, target)


def test_gc220_indexed_write_overrides_seen_name_hint_but_membership_alone_does_not():
    source = """INPUT xs
seen = {}
FOR x in xs:
    seen[x] = true
RETURN seen
"""
    result = _process(source)
    assert "seen <- EMPTY DICTIONARY" in result.processed_source
    assert any(item.rule == "GC220" for item in result.transformations)

    membership_only = """INPUT xs
seen = {}
FOR x in xs:
    IF x in seen:
        RETURN x
RETURN NONE
"""
    result = _process(membership_only)
    assert not any(item.rule == "GC220" for item in result.transformations)


def test_gc221_requires_explicit_list_backing_and_preserves_nested_argument():
    list_backed = """INPUT x
items = []
items.add((MIN(x, 3), MAX(x, 3)))
RETURN items
"""
    result = _process(list_backed)
    assert "APPEND TUPLE(CALL min(x, 3), CALL max(x, 3)) TO items" in result.processed_source
    assert any(item.rule == "GC221" for item in result.transformations)

    no_list_evidence = """INPUT x
items.add((MIN(x, 3), MAX(x, 3)))
RETURN items
"""
    result = _process(no_list_evidence)
    assert not any(item.rule == "GC221" for item in result.transformations)


def test_gc222_exact_unique_simple_identifier_maps_to_existing_to_set_intrinsic():
    source = """INPUT values
RETURN unique(values)
"""
    result, python_source = _compile(source)
    assert "RETURN CALL to_set(values)" in result.processed_source
    entries = [
        item for item in result.to_dict()["transformations"]
        if item["branch"] == "EXACT_UNIQUE_TO_SET_INTRINSIC"
    ]
    assert len(entries) == 1
    assert entries[0]["rule_family"] == "COLLECTION_DEDUPLICATION"
    assert entries[0]["confidence"] == "user_confirmed"
    assert entries[0]["semantic_change"] is False
    assert "return set(values)" in python_source


def test_gc222_does_not_rewrite_member_unique_or_multi_argument_unknown_calls():
    member = """INPUT values
RETURN values.unique()
"""
    result = _process(member)
    assert not any(item.rule == "GC222" for item in result.transformations)

    multi = """INPUT values, mode
RETURN unique(values, mode)
"""
    result = _process(multi)
    assert not any(item.rule == "GC222" for item in result.transformations)


def test_gc222_preserves_set_return_type_even_when_values_are_already_unique():
    source = """INPUT list1, list2
set1 = set(list1)
result = []
FOR item in list2:
    IF item in set1 AND item not in result:
        result.append(item)
RETURN unique(result)
"""
    result = _process(source)
    rules = [item.rule for item in result.transformations]
    assert "GC214" not in rules
    assert "GC222" in rules
    assert "RETURN CALL to_set(result)" in result.processed_source
