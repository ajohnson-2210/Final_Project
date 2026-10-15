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


def test_gc161_makes_capacity_storage_visible_in_canonical_pseudocode():
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

    assert 'CLASS LRUCache ACCEPTS(capacity)' in result.processed_source
    assert '    given_capacity <- capacity' in result.processed_source
    assert '    cache <- EMPTY DICTIONARY' in result.processed_source
    assert '    order <- EMPTY LIST' in result.processed_source

    assert 'def __init__(self, capacity):' in python_source
    assert python_source.count('self.given_capacity = capacity') == 1
    assert 'self.capacity = capacity' not in python_source
    assert 'self.cache = {}' in python_source
    assert 'self.order = []' in python_source


def test_legacy_class_explicit_parameter_state_does_not_duplicate_python_assignment():
    source = '''CLASS Box ACCEPTS(seed)
    seed <- seed
    value <- 0
ENDCLASS
'''
    parsed = AJParserFacade().parse(source)
    assert parsed.success, parsed.error
    flow = FlowDiagramEncoder().encode(parsed.ast)
    python_source = AJPythonCompiler().compile(flow).source_code

    assert python_source.count('self.seed = seed') == 1
    assert 'self.value = 0' in python_source


def test_legacy_class_without_explicit_parameter_state_keeps_backwards_compatible_lowering():
    source = '''CLASS Box ACCEPTS(seed)
    value <- 0
ENDCLASS
'''
    parsed = AJParserFacade().parse(source)
    assert parsed.success, parsed.error
    flow = FlowDiagramEncoder().encode(parsed.ast)
    python_source = AJPythonCompiler().compile(flow).source_code

    # Existing legacy surfaces still receive their historical implicit state
    # assignment unless canonicalisation has made it explicit.
    assert python_source.count('self.seed = seed') == 1
    assert 'self.value = 0' in python_source


def test_legacy_class_explicit_parameter_alias_suppresses_implicit_parameter_field():
    source = '''CLASS Box ACCEPTS(seed)
    given_seed <- seed
    value <- 0
ENDCLASS
'''
    parsed = AJParserFacade().parse(source)
    assert parsed.success, parsed.error
    flow = FlowDiagramEncoder().encode(parsed.ast)
    python_source = AJPythonCompiler().compile(flow).source_code

    assert 'self.given_seed = seed' in python_source
    assert 'self.seed = seed' not in python_source


def test_gc161_capacity_reads_follow_visible_given_capacity_state():
    source = '''CLASS LRUCache
    cache <- EMPTY DICTIONARY
    capacity <- GIVEN CAPACITY
    order <- EMPTY LIST

    FUNCTION get(key):
        RETURN 999

    FUNCTION put(key, value):
        IF LENGTH OF order >= capacity THEN
            OUTPUT value
        ENDIF
ENDCLASS
'''
    result, python_source = _compile(source)

    assert 'given_capacity <- capacity' in result.processed_source
    assert 'LENGTH OF order >= given_capacity' in result.processed_source
    assert 'len(self.order) >= self.given_capacity' in python_source
    assert 'self.capacity' not in python_source


def test_gc161_rewrites_only_executable_capacity_references_to_given_capacity():
    source = '''CLASS LRUCache
    cache <- EMPTY DICTIONARY
    capacity <- GIVEN CAPACITY
    order <- EMPTY LIST

    FUNCTION get(key):
        OUTPUT STRING("capacity")
        RETURN capacity

    FUNCTION put(key, value):
        IF LENGTH OF order >= capacity THEN // capacity limit
            OUTPUT value
        ENDIF
ENDCLASS
'''
    result, python_source = _compile(source)

    assert 'given_capacity <- capacity' in result.processed_source
    assert 'RETURN given_capacity' in result.processed_source
    assert 'LENGTH OF order >= given_capacity' in result.processed_source
    assert 'STRING("capacity")' in result.processed_source
    assert '// capacity limit' not in result.processed_source  # comment is non-executable metadata
    assert 'return self.given_capacity' in python_source
    assert 'len(self.order) >= self.given_capacity' in python_source
    assert "print('capacity')" in python_source
    assert 'self.capacity' not in python_source
