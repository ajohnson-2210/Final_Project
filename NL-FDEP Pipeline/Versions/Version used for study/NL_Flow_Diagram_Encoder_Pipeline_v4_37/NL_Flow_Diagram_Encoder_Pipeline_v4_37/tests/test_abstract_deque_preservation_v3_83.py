from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def process(source: str):
    return PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )


def compile_source(canonical: str) -> str:
    parsed = AJParserFacade().parse(canonical)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    return compiled.source_code


def test_explicit_empty_deque_preserves_deque_abstraction_and_executes():
    source = """FUNCTION slidingWindowMax(arr, k):
    result = empty list
    deque = empty deque
    FOR i FROM 0 TO length(arr)-1:
        WHILE deque IS NOT empty AND deque.front() <= i - k:
            deque.pop_front()
        WHILE deque IS NOT empty AND arr[deque.back()] <= arr[i]:
            deque.pop_back()
        deque.push_back(i)
        IF i >= k - 1:
            result.append(arr[deque.front()])
    RETURN result
"""
    result = process(source)
    canonical = result.processed_source
    assert "deque <- CALL create_deque()" in canonical
    assert "NOT CALL deque_is_empty(deque)" in canonical
    assert "CALL deque_front(deque)" in canonical
    assert "CALL deque_back(deque)" in canonical
    assert "CALL deque_pop_front(deque)" in canonical
    assert "CALL deque_pop_back(deque)" in canonical
    assert "CALL deque_push_back(deque, i)" in canonical
    assert "deque <- EMPTY LIST" not in canonical

    python_source = compile_source(canonical)
    assert "deque = []" in python_source
    assert "deque.pop(0)" in python_source
    assert "deque.pop(-1)" in python_source
    assert "deque.append(i)" in python_source
    namespace = {}
    exec(python_source, namespace)
    assert namespace["slidingWindowMax"]([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]


def test_explicit_deque_constructor_is_preserved_as_abstract_constructor():
    source = """FUNCTION build ACCEPTS(value)
    deque <- Deque()
    deque.push_back(value)
    RETURN deque
ENDFUNCTION
"""
    result = process(source)
    assert "deque <- CALL create_deque()" in result.processed_source
    assert "CALL deque_push_back(deque, value)" in result.processed_source
    python_source = compile_source(result.processed_source)
    namespace = {}
    exec(python_source, namespace)
    assert namespace["build"](7) == [7]


def test_explicit_list_backed_deque_idiom_remains_list_backed():
    source = """FUNCTION consume ACCEPTS(value)
    deque <- EMPTY LIST
    APPEND value TO back of deque
    IF deque not empty THEN
        result <- deque.back
        REMOVE back of deque
    ENDIF
    RETURN result
ENDFUNCTION
"""
    result = process(source)
    canonical = result.processed_source
    assert "deque <- EMPTY LIST" in canonical
    assert "CALL create_deque()" not in canonical
    assert "APPEND value TO deque" in canonical
    assert "result <- deque[-1]" in canonical
    assert "REMOVE LAST ITEM FROM deque" in canonical


def test_deque_member_evidence_is_invalidated_by_direct_rebind():
    source = """FUNCTION operate ACCEPTS(replacement, value)
    deque <- EMPTY DEQUE
    deque <- replacement
    deque.push_back(value)
    RETURN deque
ENDFUNCTION
"""
    result = process(source)
    assert "deque <- CALL create_deque()" in result.processed_source
    assert "deque.push_back(value)" in result.processed_source
    assert "CALL deque_push_back(deque, value)" not in result.processed_source
