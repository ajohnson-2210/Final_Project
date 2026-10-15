import unittest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


class AbstractQueuePreservationV382Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def process(self, source: str):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def compile(self, canonical: str):
        parsed = AJParserFacade().parse(canonical)
        self.assertTrue(parsed.success, parsed.error)
        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        self.assertTrue(compiled.success)
        return compiled.source_code

    def test_source_c_level_order_preserves_explicit_queue_abstraction(self):
        source = '''FUNCTION levelOrderTraversal(root):
    IF root IS NULL:
        RETURN empty list
    result = empty list
    queue = empty queue
    queue.enqueue(root)
    WHILE queue IS NOT empty:
        levelSize = queue.size()
        currentLevel = empty list
        FOR i FROM 0 TO levelSize-1:
            node = queue.dequeue()
            currentLevel.append(node.value)
            IF node.left != NULL:
                queue.enqueue(node.left)
            IF node.right != NULL:
                queue.enqueue(node.right)
        result.append(currentLevel)
    RETURN result
'''
        result = self.process(source)
        canonical = result.processed_source
        self.assertIn('queue <- CALL create_queue()', canonical)
        self.assertIn('CALL ENQUEUE(queue, root)', canonical)
        self.assertIn('WHILE NOT CALL queue_is_empty(queue) DO', canonical)
        self.assertIn('levelSize <- CALL queue_size(queue)', canonical)
        self.assertIn('node <- CALL DEQUEUE(queue)', canonical)
        self.assertIn('CALL ENQUEUE(queue, node.left)', canonical)
        self.assertIn('CALL ENQUEUE(queue, node.right)', canonical)
        self.assertNotIn('queue <- EMPTY LIST', canonical)
        self.assertNotIn('REMOVE FIRST ITEM FROM queue', canonical)

        python_source = self.compile(canonical)
        self.assertIn('queue = []', python_source)
        self.assertIn('queue.append(root)', python_source)
        self.assertIn('node = queue.pop(0)', python_source)
        self.assertIn('levelSize = len(queue)', python_source)

        namespace = {}
        exec(python_source, namespace)
        root = Node(1, Node(2, Node(4), Node(5)), Node(3))
        self.assertEqual([[1], [2, 3], [4, 5]], namespace['levelOrderTraversal'](root))
        self.assertEqual([], namespace['levelOrderTraversal'](None))

    def test_explicit_list_fifo_compatibility_remains_list_backed(self):
        source = '''FUNCTION f ACCEPTS(value)
    queue <- EMPTY LIST
    ENQUEUE value TO queue
    item <- DEQUEUE FROM queue
    RETURN item
ENDFUNCTION
'''
        result = self.process(source)
        canonical = result.processed_source
        self.assertIn('queue <- EMPTY LIST', canonical)
        self.assertIn('APPEND value TO queue', canonical)
        self.assertIn('item <- REMOVE FIRST ITEM FROM queue', canonical)
        self.assertNotIn('CALL create_queue()', canonical)

    def test_anonymous_create_empty_queue_uses_queue_intrinsics(self):
        source = '''BEGIN
    INPUT Root
    CREATE Empty Queue
    ENQUEUE Root
    WHILE Queue is not empty
        Node <- DEQUEUE Queue
        OUTPUT Node.Value
    ENDWHILE
END
'''
        result = self.process(source)
        canonical = result.processed_source
        self.assertIn('Queue <- CALL create_queue()', canonical)
        self.assertIn('CALL ENQUEUE(Queue, Root)', canonical)
        self.assertIn('WHILE NOT CALL queue_is_empty(Queue) DO', canonical)
        self.assertIn('Node <- CALL DEQUEUE(Queue)', canonical)
        self.assertNotIn('Queue <- EMPTY LIST', canonical)

        python_source = self.compile(canonical)
        self.assertIn('Queue = []', python_source)
        self.assertIn('Queue.append(Root)', python_source)
        self.assertIn('Node = Queue.pop(0)', python_source)

    def test_compiler_lowers_nested_dequeue_enqueue_with_temporary(self):
        canonical = '''FUNCTION transfer ACCEPTS()
    source <- CALL create_queue()
    target <- CALL create_queue()
    CALL ENQUEUE(source, 1)
    CALL ENQUEUE(target, CALL DEQUEUE(source))
    RETURN CALL DEQUEUE(target)
ENDFUNCTION
'''
        python_source = self.compile(canonical)
        self.assertIn('temp = source.pop(0)', python_source)
        self.assertIn('target.append(temp)', python_source)
        namespace = {}
        exec(python_source, namespace)
        self.assertEqual(1, namespace['transfer']())


if __name__ == '__main__':
    unittest.main()
