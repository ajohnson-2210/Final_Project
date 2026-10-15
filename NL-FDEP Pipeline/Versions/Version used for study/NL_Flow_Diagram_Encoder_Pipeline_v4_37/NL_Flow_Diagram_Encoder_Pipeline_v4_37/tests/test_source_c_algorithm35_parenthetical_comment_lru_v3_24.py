import random

from pseudocode_profiles import GenericPseudocodeProcessor
from aj_parser import AJParserFacade
from flow_diagram import FlowDiagramEncoder
from aj_python_compiler import AJPythonCompiler


source_c_35 = '''CLASS LRUCache:
    // Use a combination of a dictionary and a doubly linked list (or an ordered map)
    cache = empty dictionary
    capacity = given capacity
    order = empty list (or a doubly linked list to maintain access order)

    FUNCTION get(key):
        IF key NOT IN cache:
            RETURN -1 // or NULL
        // Move key to front of order (most recently used)
        order.remove(key)
        order.insert_front(key)
        RETURN cache[key]

    FUNCTION put(key, value):
        IF key IN cache:
            // Update value and move key to front
            cache[key] = value
            order.remove(key)
            order.insert_front(key)
        ELSE:
            IF length(order) >= capacity:
                // Evict the least recently used (last element in order)
                lruKey = order.back()
                order.remove_back()
                cache.remove(lruKey)
            order.insert_front(key)
            cache[key] = value
'''


def _compile(source=source_c_35):
    result = GenericPseudocodeProcessor().process(source)
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    flow = FlowDiagramEncoder().encode(parsed.ast)
    compiled = AJPythonCompiler().compile(flow)
    namespace = {}
    exec(compiled.source_code, namespace)
    return result, compiled.source_code, namespace


def test_gc226_detaches_trailing_explanatory_parenthetical_before_collection_parsing():
    result = GenericPseudocodeProcessor().process(source_c_35)
    assert any(t.rule == 'GC226' for t in result.transformations)
    assert 'order <- EMPTY LIST' in result.processed_source
    assert 'EMPTY CALL to_list' not in result.processed_source
    assert 'doubly linked list to maintain access order' not in result.processed_source


def test_exact_source_c_35_reaches_existing_lru_recovery_and_compiles():
    result, python_source, _ = _compile()
    assert any(t.rule == 'GC161' for t in result.transformations)
    assert 'CLASS LRUCache ACCEPTS(capacity)' in result.processed_source
    assert 'given_capacity <- capacity' in result.processed_source
    assert 'def __init__(self, capacity):' in python_source
    assert 'self.cache = {}' in python_source
    assert 'self.order = []' in python_source
    assert 'self.order.insert(0, key)' in python_source
    assert 'self.order.pop()' in python_source
    assert 'self.cache.pop(lruKey)' in python_source


def test_gc226_does_not_strip_grouped_arithmetic_parentheses():
    source = '''FUNCTION midpoint ACCEPTS(low, high)
    mid <- (low + high) INTEGER DIVISION 2
    RETURN mid
ENDFUNCTION'''
    result = GenericPseudocodeProcessor().process(source)
    assert '(low + high) INTEGER DIVISION 2' in result.processed_source
    assert not any(t.rule == 'GC226' for t in result.transformations)


def test_gc226_does_not_strip_non_comment_parenthetical_after_empty_list():
    source = '''FUNCTION f ACCEPTS()
    items <- empty list (x + y)
    RETURN items
ENDFUNCTION'''
    result = GenericPseudocodeProcessor().process(source)
    assert not any(t.rule == 'GC226' for t in result.transformations)


def test_gc226_accepts_for_annotation_on_complete_empty_collection_initializer():
    source = '''CLASS QueueUsingStacks:
    stack1 = empty stack (for enqueue)
    stack2 = empty stack (for dequeue)
'''
    result = GenericPseudocodeProcessor().process(source)
    gc226 = [t for t in result.transformations if t.rule == 'GC226']
    assert len(gc226) == 2
    assert all('(for ' in t.source for t in gc226)


def test_recovered_source_c_35_matches_reference_lru_random_sequences():
    _, _, namespace = _compile()
    LRUCache = namespace['LRUCache']

    for capacity in range(1, 6):
        rng = random.Random(3500 + capacity)
        actual = LRUCache(capacity)
        reference_values = {}
        reference_order = []  # LRU -> MRU

        for _ in range(300):
            key = rng.randrange(7)
            if rng.random() < 0.58:
                value = rng.randrange(-20, 21)
                actual.put(key, value)
                if key in reference_values:
                    reference_order.remove(key)
                elif len(reference_order) >= capacity:
                    evicted = reference_order.pop(0)
                    reference_values.pop(evicted)
                reference_values[key] = value
                reference_order.append(key)
            else:
                got = actual.get(key)
                expected = reference_values.get(key, -1)
                assert got == expected
                if key in reference_values:
                    reference_order.remove(key)
                    reference_order.append(key)

            assert actual.cache == reference_values
            assert actual.order == list(reversed(reference_order))
