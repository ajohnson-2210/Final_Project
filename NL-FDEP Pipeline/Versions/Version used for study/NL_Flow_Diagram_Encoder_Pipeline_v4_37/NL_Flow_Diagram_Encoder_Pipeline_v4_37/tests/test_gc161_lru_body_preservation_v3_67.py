from pseudocode_profiles import GenericPseudocodeProcessor
from aj_parser import AJParserFacade
from flow_diagram import FlowDiagramEncoder
from aj_python_compiler import AJPythonCompiler


def _compile(source: str):
    result = GenericPseudocodeProcessor().process(source)
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    flow = FlowDiagramEncoder().encode(parsed.ast)
    compiled = AJPythonCompiler().compile(flow)
    return result, compiled.source_code


def test_gc161_preserves_source_written_get_and_put_bodies():
    source = '''CLASS LRUCache
    cache <- EMPTY DICTIONARY
    capacity <- GIVEN CAPACITY
    order <- EMPTY LIST

    FUNCTION get(key):
        RETURN 999

    FUNCTION put(key, value):
        OUTPUT value
ENDCLASS
'''
    result, python_source = _compile(source)

    assert any(t.rule == 'GC161' for t in result.transformations)
    assert 'CLASS LRUCache ACCEPTS(capacity)' in result.processed_source
    assert 'given_capacity <- capacity' in result.processed_source
    assert 'RETURN 999' in result.processed_source
    assert 'OUTPUT value' in result.processed_source

    # The historical stock implementation must not be manufactured.
    assert 'IF key NOT IN cache THEN' not in result.processed_source
    assert 'CALL remove_from_list(order, key)' not in result.processed_source
    assert 'CALL insert_front(order, key)' not in result.processed_source
    assert 'CALL remove_last_from_list(order)' not in result.processed_source

    assert 'def get(self, key):' in python_source
    assert 'return 999' in python_source
    assert 'def put(self, key, value):' in python_source
    assert 'print(value)' in python_source
    assert 'self.order.remove(key)' not in python_source
    assert 'self.order.insert(0, key)' not in python_source


def test_gc161_keeps_explicit_lru_operations_but_does_not_add_steps():
    source = '''CLASS LRUCache
    cache <- EMPTY DICTIONARY
    capacity <- GIVEN CAPACITY
    order <- EMPTY LIST

    FUNCTION get(key):
        order.remove(key)
        RETURN cache[key]

    FUNCTION put(key, value):
        order.insert_front(key)
        cache[key] <- value
ENDCLASS
'''
    result, python_source = _compile(source)

    assert 'CALL remove_from_list(order, key)' in result.processed_source
    assert 'CALL insert_front(order, key)' in result.processed_source
    assert 'RETURN cache[key]' in result.processed_source
    assert 'cache[key] <- value' in result.processed_source

    # No eviction/missing-key branch was present in the source, so none appears.
    assert 'IF key NOT IN cache THEN' not in result.processed_source
    assert 'LENGTH OF order >= capacity' not in result.processed_source
    assert 'remove_last_from_list' not in result.processed_source

    assert 'self.order.remove(key)' in python_source
    assert 'self.order.insert(0, key)' in python_source
    assert 'return self.cache[key]' in python_source
    assert 'self.cache[key] = value' in python_source


def test_explicit_non_lru_method_bodies_remain_arbitrary_source_logic():
    source = '''CLASS LRUCache
    cache <- EMPTY DICTIONARY
    capacity <- GIVEN CAPACITY
    order <- EMPTY LIST

    FUNCTION get(key):
        OUTPUT key
        RETURN 17

    FUNCTION put(key, value):
        RETURN value
ENDCLASS
'''
    result, python_source = _compile(source)

    assert 'OUTPUT key' in result.processed_source
    assert 'RETURN 17' in result.processed_source
    assert 'RETURN value' in result.processed_source
    assert 'IF key IN cache THEN' not in result.processed_source

    assert 'print(key)' in python_source
    assert 'return 17' in python_source
    assert 'return value' in python_source
