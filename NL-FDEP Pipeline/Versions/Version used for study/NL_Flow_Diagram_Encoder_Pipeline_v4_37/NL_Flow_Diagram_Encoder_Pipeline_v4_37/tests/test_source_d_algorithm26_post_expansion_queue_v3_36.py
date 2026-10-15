from pseudocode_profiles import GenericPseudocodeProcessor
from aj_parser import AJParserFacade
from flow_diagram import FlowDiagramEncoder
from aj_python_compiler import AJPythonCompiler


source_d_26 = '''FUNCTION LevelOrderTraversal(root):
    IF root IS NULL THEN RETURN empty List

    result = empty List
    queue = empty Queue
    ENQUEUE root TO queue

    WHILE queue IS NOT EMPTY DO
        level_size = queue.size()
        current_level = empty List

        FOR i FROM 1 TO level_size DO
            node = DEQUEUE from queue
            APPEND node.value TO current_level

            IF node.left IS NOT NULL THEN ENQUEUE node.left TO queue
            IF node.right IS NOT NULL THEN ENQUEUE node.right TO queue
        END FOR

        APPEND current_level TO result
    END WHILE

    RETURN result
END FUNCTION
'''


class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


def _compile(source=source_d_26):
    result = GenericPseudocodeProcessor().process(source)
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    flow = FlowDiagramEncoder().encode(parsed.ast)
    compiled = AJPythonCompiler().compile(flow)
    namespace = {}
    exec(compiled.source_code, namespace)
    return result, compiled.source_code, namespace


def test_gc235_recovers_queue_ops_exposed_by_one_line_if_expansion():
    result, python_source, namespace = _compile()
    gc235 = [t for t in result.transformations if t.rule == 'GC235']
    assert len(gc235) == 2
    assert 'ENQUEUE node.left TO queue' not in result.processed_source
    assert 'ENQUEUE node.right TO queue' not in result.processed_source
    assert 'CALL ENQUEUE(queue, node.left)' in result.processed_source
    assert 'CALL ENQUEUE(queue, node.right)' in result.processed_source
    assert 'queue.append(node.left)' in python_source
    assert 'queue.append(node.right)' in python_source

    root = Node(1, Node(2, Node(4), Node(5)), Node(3))
    assert namespace['LevelOrderTraversal'](root) == [[1], [2, 3], [4, 5]]
    assert namespace['LevelOrderTraversal'](None) == []


def test_gc235_refuses_unproven_receiver_after_one_line_if_expansion():
    source = '''FUNCTION f ACCEPTS(queue, condition, value)
    IF condition THEN ENQUEUE value TO queue
    RETURN queue
ENDFUNCTION
'''
    result = GenericPseudocodeProcessor().process(source)
    assert not any(t.rule == 'GC235' for t in result.transformations)
    assert 'ENQUEUE value TO queue' in result.processed_source


def test_gc235_evidence_is_lexical_routine_local():
    source = '''FUNCTION seed ACCEPTS()
    queue <- EMPTY LIST
    RETURN queue
ENDFUNCTION
FUNCTION use ACCEPTS(queue, condition, value)
    IF condition THEN ENQUEUE value TO queue
    RETURN queue
ENDFUNCTION
'''
    result = GenericPseudocodeProcessor().process(source)
    assert not any(t.rule == 'GC235' for t in result.transformations)
    assert 'ENQUEUE value TO queue' in result.processed_source


def test_gc235_direct_reassignment_invalidates_list_backing_evidence():
    source = '''FUNCTION f ACCEPTS(condition, value, replacement)
    queue <- EMPTY LIST
    queue <- replacement
    IF condition THEN ENQUEUE value TO queue
    RETURN queue
ENDFUNCTION
'''
    result = GenericPseudocodeProcessor().process(source)
    assert not any(t.rule == 'GC235' for t in result.transformations)
    assert 'ENQUEUE value TO queue' in result.processed_source
