from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_f_ALGORITHM_35 = '''INIT capacity, cache = orderedDict()

FUNCTION get(key):
    IF key in cache:
        moveToFront(cache, key)
        RETURN cache[key]
    ELSE:
        RETURN null

FUNCTION put(key, value):
    IF key in cache:
        moveToFront(cache, key)
        cache[key] = value
    ELSE:
        IF length(cache) == capacity:
            removeBack(cache)

        addToFront(cache, key, value)
'''


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def _compile_result(processed_source: str):
    parsed = AJParserFacade().parse(processed_source)
    assert parsed.success, parsed.error
    return AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))


def test_source_f35_recovers_class_but_preserves_undefined_ordering_abstractions():
    result = _process(source_f_ALGORITHM_35)

    assert "CLASS unnamed_class" in result.processed_source
    assert "PROPERTY capacity" in result.processed_source
    assert "PROPERTY cache AS DICTIONARY" in result.processed_source
    assert "CONSTRUCTOR ACCEPTS(capacity)" in result.processed_source
    assert "PROPERTY THIS.capacity <- capacity" in result.processed_source
    assert "PROPERTY THIS.cache <- EMPTY DICTIONARY" in result.processed_source
    assert "METHOD get ACCEPTS(key)" in result.processed_source
    assert "METHOD put ACCEPTS(key, value)" in result.processed_source
    assert "CALL moveToFront(THIS.cache, key)" in result.processed_source
    assert "CALL removeBack(THIS.cache)" in result.processed_source
    assert "CALL addToFront(THIS.cache, key, value)" in result.processed_source
    assert "THIS.cache[key] <- value" in result.processed_source

    # GC215 may recover structure, but it must not implement the abstract
    # recency operations.
    assert "move_key_to_back" not in result.processed_source
    assert "remove_first_mapping" not in result.processed_source
    assert "orderedDict" not in result.processed_source

    gc215 = [item for item in result.transformations if item.rule == "GC215"]
    assert len(gc215) == 1

    compiled = _compile_result(result.processed_source)
    assert not compiled.success
    assert compiled.source_code == ""
    assert "unresolved source abstraction" in compiled.message
    assert "moveToFront" in compiled.message
    assert "removeBack" in compiled.message
    assert "addToFront" in compiled.message


def test_gc215_audit_reports_source_proven_stateful_adt_recovery():
    result = _process(source_f_ALGORITHM_35)
    entries = [
        item for item in result.to_dict()["transformations"]
        if item["branch"] == "EVIDENCED_ORDERED_CACHE_CONSTRUCTOR"
    ]
    assert len(entries) == 1
    assert entries[0]["rule_family"] == "STATEFUL_ADT_STRUCTURE"
    assert entries[0]["confidence"] == "source_proven"
    assert entries[0]["semantic_change"] is False


def test_gc215_is_not_hardcoded_to_capacity_cache_get_put_names():
    source = '''INIT limit, store = orderedDict()
FUNCTION read(k):
    IF k in store:
        moveToFront(store, k)
        RETURN store[k]
    ELSE:
        RETURN null
FUNCTION write(k, v):
    IF k in store:
        moveToFront(store, k)
        store[k] = v
    ELSE:
        IF length(store) == limit:
            removeBack(store)
        addToFront(store, k, v)
'''
    result = _process(source)
    assert "PROPERTY limit" in result.processed_source
    assert "PROPERTY store AS DICTIONARY" in result.processed_source
    assert "CONSTRUCTOR ACCEPTS(limit)" in result.processed_source
    assert "METHOD read ACCEPTS(k)" in result.processed_source
    assert "METHOD write ACCEPTS(k, v)" in result.processed_source
    assert any(item.rule == "GC215" for item in result.transformations)


def test_gc215_refuses_unrelated_multi_target_init():
    source = '''INIT count, values = orderedDict()
FUNCTION first(key):
    RETURN values[key]
FUNCTION second(key):
    RETURN values[key]
'''
    result = _process(source)
    assert not any(item.rule == "GC215" for item in result.transformations)
    assert "INIT count, values" in result.processed_source


def test_gc215_refuses_move_to_front_without_membership_proof():
    source = source_f_ALGORITHM_35.replace(
        "    IF key in cache:\n        moveToFront(cache, key)\n        RETURN cache[key]",
        "    moveToFront(cache, key)\n    RETURN cache[key]",
        1,
    )
    result = _process(source)
    assert not any(item.rule == "GC215" for item in result.transformations)


def test_gc215_refuses_remove_back_without_fullness_guard():
    source = source_f_ALGORITHM_35.replace(
        "        IF length(cache) == capacity:\n            removeBack(cache)",
        "        removeBack(cache)",
    )
    result = _process(source)
    assert not any(item.rule == "GC215" for item in result.transformations)


def test_gc215_refuses_add_to_front_outside_absent_key_branch():
    source = source_f_ALGORITHM_35.replace(
        "\n        addToFront(cache, key, value)",
        "\n    addToFront(cache, key, value)",
    )
    result = _process(source)
    assert not any(item.rule == "GC215" for item in result.transformations)


def test_gc215_refuses_unknown_call_escape():
    source = source_f_ALGORITHM_35.replace(
        "        moveToFront(cache, key)\n        RETURN cache[key]",
        "        inspect(cache)\n        moveToFront(cache, key)\n        RETURN cache[key]",
        1,
    )
    result = _process(source)
    assert not any(item.rule == "GC215" for item in result.transformations)


def test_gc215_does_not_emit_python_for_undefined_ordering_helpers():
    result = _process(source_f_ALGORITHM_35)
    compiled = _compile_result(result.processed_source)
    assert not compiled.success
    assert compiled.source_code == ""
    assert compiled.execution_model == "STRUCTURED"

