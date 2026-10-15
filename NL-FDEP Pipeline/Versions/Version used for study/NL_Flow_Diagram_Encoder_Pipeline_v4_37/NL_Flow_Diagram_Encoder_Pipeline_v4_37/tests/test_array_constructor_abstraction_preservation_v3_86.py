from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )


def _compile(source: str):
    processed = _process(source)
    parsed = AJParserFacade().parse(processed.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    return processed, compiled.source_code


def test_array_conversion_preserves_array_abstraction_but_uses_mutable_python_backing():
    source = '''FUNCTION reverse ACCEPTS(s)
    chars = array(s)
    left = 0
    right = LENGTH(s) - 1
    WHILE left < right
        SWAP chars[left] AND chars[right]
        left = left + 1
        right = right - 1
    ENDWHILE
    RETURN JOIN(chars, EMPTY STRING)
ENDFUNCTION
'''
    processed, python_source = _compile(source)
    assert 'chars <- CALL to_array(s)' in processed.processed_source
    assert 'CALL to_list(s)' not in processed.processed_source
    assert 'chars = list(s)' in python_source

    namespace = {}
    exec(python_source, namespace)
    assert namespace['reverse']('abcd') == 'dcba'


def test_list_and_set_constructors_keep_their_own_abstractions():
    source = '''FUNCTION convert ACCEPTS(items)
    values = list(items)
    unique = set(items)
    RETURN TUPLE(values, unique)
ENDFUNCTION
'''
    processed, python_source = _compile(source)
    assert 'values <- CALL to_list(items)' in processed.processed_source
    assert 'unique <- CALL to_set(items)' in processed.processed_source
    assert 'CALL to_array(items)' not in processed.processed_source
    assert 'values = list(items)' in python_source
    assert 'unique = set(items)' in python_source


def test_named_stack_and_queue_constructors_are_not_relabelled_as_arrays_or_lists():
    source = '''FUNCTION keep ACCEPTS()
    stack <- Stack()
    queue <- Queue()
    RETURN TUPLE(stack, queue)
ENDFUNCTION
'''
    processed = _process(source)
    canonical = processed.processed_source
    assert 'stack <- CALL Stack()' in canonical
    assert 'queue <- CALL Queue()' in canonical
    assert 'CALL to_array(' not in canonical
    assert 'CALL to_list(' not in canonical


def test_ordered_dict_constructor_is_not_reclassified():
    source = '''FUNCTION keep ACCEPTS()
    cache <- orderedDict()
    RETURN cache
ENDFUNCTION
'''
    processed = _process(source)
    assert 'cache <- CALL orderedDict()' in processed.processed_source
    assert 'EMPTY DICTIONARY' not in processed.processed_source


def test_ordered_dictionary_phrase_preserves_ordered_mapping_abstraction():
    source = '''FUNCTION make ACCEPTS()
    cache <- ordered dictionary
    RETURN cache
ENDFUNCTION
'''
    processed, python_source = _compile(source)
    assert 'cache <- CALL create_ordered_dictionary()' in processed.processed_source
    assert 'cache <- EMPTY DICTIONARY' not in processed.processed_source
    assert 'cache = {}' in python_source


def test_plain_dictionary_and_hash_map_remain_plain_dictionary():
    source = '''FUNCTION make ACCEPTS()
    first <- empty dictionary
    second <- empty hash map
    RETURN TUPLE(first, second)
ENDFUNCTION
'''
    processed, python_source = _compile(source)
    assert 'first <- EMPTY DICTIONARY' in processed.processed_source
    assert 'second <- EMPTY DICTIONARY' in processed.processed_source
    assert 'CALL create_ordered_dictionary()' not in processed.processed_source
    assert 'first = {}' in python_source
    assert 'second = {}' in python_source
