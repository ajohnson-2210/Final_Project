from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


SOURCE = '''FUNCTION SlidingWindowMaximum(arr, k):
    result = empty List
    deque = empty DoubleEndedQueue // Stores indices
    
    FOR i FROM 0 TO length(arr) - 1 DO
        IF deque IS NOT EMPTY AND deque.front() <= i - k THEN
            REMOVE FRONT FROM deque
        END IF
        
        WHILE deque IS NOT EMPTY AND arr[deque.back()] <= arr[i] DO
            REMOVE BACK FROM deque
        END WHILE
        
        ADD BACK i TO deque
        
        IF i >= k - 1 THEN
            APPEND arr[deque.front()] TO result
        END IF
    END FOR
    
    RETURN result
END FUNCTION
'''


def process(source=SOURCE):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def compile_source(result):
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    diagram = FlowDiagramEncoder().encode(parsed.ast)
    compiled = AJPythonCompiler().compile(diagram)
    assert compiled.success
    return compiled.source_code


def test_source_d_algorithm28_recovers_only_explicit_deque_surface_operations():
    result = process()

    assert "deque <- CALL create_deque()" in result.processed_source
    assert "COMMENT Stores indices" in result.processed_source
    assert "CALL deque_pop_front(deque)" in result.processed_source
    assert "CALL deque_pop_back(deque)" in result.processed_source
    assert "CALL deque_push_back(deque, i)" in result.processed_source
    assert "REMOVE FRONT FROM deque" not in result.processed_source
    assert "REMOVE BACK FROM deque" not in result.processed_source
    assert "ADD BACK i TO deque" not in result.processed_source
    assert sum(t.rule == "GC237" for t in result.transformations) == 3


def test_source_d_algorithm28_executes_expected_sliding_window_behaviour():
    result = process()
    python_source = compile_source(result)
    namespace = {}
    exec(python_source, namespace)

    fn = namespace["SlidingWindowMaximum"]
    assert fn([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
    assert fn([1], 1) == [1]
    assert fn([9, 8, 7], 2) == [9, 8]


def test_gc237_refuses_same_vocabulary_without_explicit_deque_evidence():
    source = '''FUNCTION Example ACCEPTS(items, value)
REMOVE FRONT FROM items
REMOVE BACK FROM items
ADD BACK value TO items
RETURN items
ENDFUNCTION
'''
    result = process(source)

    assert "REMOVE FRONT FROM items" in result.processed_source
    assert "REMOVE BACK FROM items" in result.processed_source
    assert "APPEND BACK value TO items" in result.processed_source
    assert not any(t.rule == "GC237" for t in result.transformations)


def test_gc237_evidence_is_routine_local():
    source = '''FUNCTION make ACCEPTS()
deque <- EMPTY DEQUE
RETURN deque
ENDFUNCTION
FUNCTION use ACCEPTS(deque, value)
ADD BACK value TO deque
RETURN deque
ENDFUNCTION
'''
    result = process(source)

    assert "APPEND BACK value TO deque" in result.processed_source
    assert not any(t.rule == "GC237" for t in result.transformations)


def test_gc237_direct_reassignment_invalidates_deque_evidence():
    source = '''FUNCTION Example ACCEPTS(other, value)
deque <- EMPTY DEQUE
deque <- other
ADD BACK value TO deque
RETURN deque
ENDFUNCTION
'''
    result = process(source)

    assert "APPEND BACK value TO deque" in result.processed_source
    assert not any(t.rule == "GC237" for t in result.transformations)
