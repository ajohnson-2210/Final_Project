from pseudocode_profiles import (
    GenericCollectionNormaliser,
    PseudocodeProfile,
    PseudocodeProfileProcessor,
)


SIMPLE_RULES = {"GC033", "GC034", "GC035", "GC036", "GC037", "GC038", "GC039"}


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def test_explicit_collection_evidence_preserves_all_simple_method_aliases():
    source = '''FUNCTION operate ACCEPTS(value)
    items <- EMPTY LIST
    seen <- EMPTY SET
    queue <- EMPTY QUEUE
    deque <- EMPTY DEQUE
    stack <- EMPTY STACK
    items.append(value)
    seen.add(value)
    queue.enqueue(value)
    item <- queue.dequeue()
    deque.push_back(value)
    first <- deque.pop_front()
    last <- deque.pop_back()
    stack.push(value)
    RETURN items
ENDFUNCTION
'''
    result = _process(source)
    expected = (
        "APPEND value TO items",
        "CALL add_to_set(seen, value)",
        "CALL ENQUEUE(queue, value)",
        "item <- CALL DEQUEUE(queue)",
        "CALL deque_push_back(deque, value)",
        "first <- CALL deque_pop_front(deque)",
        "last <- CALL deque_pop_back(deque)",
        "CALL PUSH(value, stack)",
    )
    for fragment in expected:
        assert fragment in result.processed_source
    assert SIMPLE_RULES.issubset({item.rule for item in result.transformations})


def test_unproven_receiver_method_spelling_does_not_establish_collection_type():
    source = '''FUNCTION operate ACCEPTS(obj, value)
    obj.append(value)
    obj.add(value)
    obj.enqueue(value)
    item <- obj.dequeue()
    obj.push(value)
    first <- obj.pop_front()
    last <- obj.pop_back()
ENDFUNCTION
'''
    result = _process(source)
    assert not SIMPLE_RULES.intersection(item.rule for item in result.transformations)
    for original in (
        "obj.append(value)",
        "obj.add(value)",
        "obj.enqueue(value)",
        "obj.dequeue()",
        "obj.push(value)",
        "obj.pop_front()",
        "obj.pop_back()",
    ):
        assert original in result.processed_source


def test_direct_rebind_invalidates_simple_collection_method_evidence():
    source = '''FUNCTION operate ACCEPTS(value, replacement)
    items <- EMPTY LIST
    items <- replacement
    items.append(value)
ENDFUNCTION
'''
    result = _process(source)
    assert "items.append(value)" in result.processed_source
    assert not any(item.rule == "GC033" for item in result.transformations)


def test_parameter_shadowing_blocks_inherited_collection_evidence():
    source = '''items <- EMPTY LIST
FUNCTION operate ACCEPTS(items, value)
    items.append(value)
ENDFUNCTION
'''
    result = _process(source)
    assert "items.append(value)" in result.processed_source
    assert not any(item.rule == "GC033" for item in result.transformations)


def test_sibling_routine_restores_enclosing_evidence_after_shadowed_routine():
    source = '''items <- EMPTY LIST
FUNCTION shadowed ACCEPTS(items, value)
    items.append(value)
FUNCTION visible ACCEPTS(value)
    items.append(value)
'''
    result = _process(source)
    assert result.processed_source.count("APPEND value TO items") == 1
    assert result.processed_source.count("items.append(value)") == 1
    assert sum(item.rule == "GC033" for item in result.transformations) == 1


def test_future_declaration_does_not_back_prove_earlier_method_call():
    source = '''FUNCTION operate ACCEPTS(obj, value)
    obj.append(value)
    obj <- EMPTY LIST
ENDFUNCTION
'''
    result = _process(source)
    assert "obj.append(value)" in result.processed_source
    assert not any(item.rule == "GC033" for item in result.transformations)


def test_collection_evidence_isolated_between_classes():
    source = '''CLASS First:
    items <- EMPTY LIST
    FUNCTION add(value):
        items.append(value)
END CLASS
CLASS Second:
    FUNCTION add(value):
        items.append(value)
END CLASS
'''
    normalised, transformations = GenericCollectionNormaliser().process(source)
    assert normalised.count("APPEND value TO items") == 1
    assert normalised.count("items.append(value)") == 1
    assert sum(item.rule == "GC033" for item in transformations) == 1


def test_explicit_typed_parameter_is_valid_receiver_evidence():
    source = '''FUNCTION collect ACCEPTS(items AS LIST, value)
    items.append(value)
ENDFUNCTION
'''
    normalised, transformations = GenericCollectionNormaliser().process(source)
    assert "APPEND value TO items" in normalised
    assert any(item.rule == "GC033" for item in transformations)
