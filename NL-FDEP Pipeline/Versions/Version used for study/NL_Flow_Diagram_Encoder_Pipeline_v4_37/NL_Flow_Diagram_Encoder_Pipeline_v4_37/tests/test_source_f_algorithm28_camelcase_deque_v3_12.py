import pytest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


SOURCE = '''INPUT arr, k

result = []
deque = []

FOR i from 0 to length(arr)-1:
    IF deque[0] == i - k:
        deque.popFront()

    WHILE deque not empty AND arr[deque.back()] <= arr[i]:
        deque.popBack()

    deque.pushBack(i)

    IF i >= k - 1:
        result.append(arr[deque.front()])

RETURN result
'''


def _process(source=SOURCE):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def _compile(result):
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    return compiled.source_code


def test_source_f_algorithm28_recovers_evidenced_camelcase_deque_operations_only():
    result = _process()

    assert 'deque <- EMPTY LIST' in result.processed_source
    assert 'REMOVE FIRST ITEM FROM deque' in result.processed_source
    assert 'REMOVE LAST ITEM FROM deque' in result.processed_source
    assert 'APPEND i TO deque' in result.processed_source
    assert 'deque.popFront' not in result.processed_source
    assert 'deque.popBack' not in result.processed_source
    assert 'deque.pushBack' not in result.processed_source
    assert sum(item.rule == 'GC213' for item in result.transformations) == 3

    audit = result.to_dict()['transformations']
    recovered = [item for item in audit if item['branch'] == 'EVIDENCED_LIST_DEQUE_METHOD']
    assert len(recovered) == 3
    assert all(item['semantic_change'] is False for item in recovered)


def test_source_f_algorithm28_keeps_missing_empty_deque_guard_and_expected_index_failure():
    result = _process()
    assert 'IF deque[0] == i - k THEN' in result.processed_source
    assert 'IF LENGTH OF deque > 0 AND deque[0] == i - k THEN' not in result.processed_source

    python_source = _compile(result)
    namespace = {}
    exec(python_source, namespace)

    with pytest.raises(IndexError, match='list index out of range'):
        namespace['unnamed_function']([1, 3, -1, -3, 5, 3, 6, 7], 3)


def test_source_f_algorithm28_representation_fix_is_sufficient_once_source_guard_is_explicit():
    guarded = SOURCE.replace(
        'IF deque[0] == i - k:',
        'IF deque not empty AND deque[0] == i - k:',
    )
    result = _process(guarded)
    python_source = _compile(result)
    namespace = {}
    exec(python_source, namespace)

    fn = namespace['unnamed_function']
    assert fn([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
    assert fn([1], 1) == [1]
    assert fn([9, 8, 7], 2) == [9, 8]


def test_gc213_does_not_rewrite_same_method_names_without_list_backing_evidence():
    source = '''FUNCTION use_widget ACCEPTS(widget, item)
widget.popFront()
widget.popBack()
widget.pushBack(item)
ENDFUNCTION
'''
    result = _process(source)

    assert 'widget.popFront()' in result.processed_source
    assert 'widget.popBack()' in result.processed_source
    assert 'widget.pushBack(item)' in result.processed_source
    assert not any(item.rule == 'GC213' for item in result.transformations)


def test_gc213_preserves_balanced_nested_pushback_argument_on_evidenced_list():
    source = '''FUNCTION add_item ACCEPTS(value)
deque <- EMPTY LIST
deque.pushBack(CALL wrap(value))
RETURN deque
ENDFUNCTION
'''
    result = _process(source)

    assert 'APPEND CALL wrap(value) TO deque' in result.processed_source
    assert any(item.rule == 'GC213' for item in result.transformations)
