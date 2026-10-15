from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_c_ALGORITHM_28 = '''FUNCTION slidingWindowMax(arr, k):
    result = empty list
    deque = empty deque
    FOR i FROM 0 TO length(arr)-1:
        // Remove elements out of window from front
        WHILE deque IS NOT empty AND deque.front() <= i - k:
            deque.pop_front()
        // Maintain decreasing order in deque
        WHILE deque IS NOT empty AND arr[deque.back()] <= arr[i]:
            deque.pop_back()
        deque.push_back(i)
        // Add max to result once window is full
        IF i >= k - 1:
            result.append(arr[deque.front()])
    RETURN result
'''


def test_source_c_algorithm28_uses_general_evidenced_nested_list_append_recovery():
    result = PseudocodeProfileProcessor().process(
        source_c_ALGORITHM_28,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )

    assert "result <- EMPTY LIST" in result.processed_source
    assert "deque <- CALL create_deque()" in result.processed_source
    assert "APPEND arr[CALL deque_front(deque)] TO result" in result.processed_source
    assert "CALL deque_pop_front(deque)" in result.processed_source
    assert "CALL deque_pop_back(deque)" in result.processed_source
    assert "CALL deque_push_back(deque, i)" in result.processed_source
    assert "deque <- EMPTY LIST" not in result.processed_source
    assert "result.append" not in result.processed_source
    assert any(t.rule == "GC200" for t in result.transformations)

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))

    namespace = {}
    exec(compiled.source_code, namespace)
    fn = namespace["slidingWindowMax"]
    assert fn([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
    assert fn([1], 1) == [1]
    assert fn([9, 8, 7], 2) == [9, 8]
