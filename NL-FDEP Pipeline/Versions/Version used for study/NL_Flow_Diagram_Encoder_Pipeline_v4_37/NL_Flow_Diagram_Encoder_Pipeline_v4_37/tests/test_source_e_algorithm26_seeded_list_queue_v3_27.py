from pseudocode_profiles import GenericPseudocodeProcessor
from aj_parser import AJParserFacade
from flow_diagram import FlowDiagramEncoder
from aj_python_compiler import AJPythonCompiler


source_e_26 = '''FUNCTION LEVEL_ORDER_TRAVERSAL(root)
  result = []
  queue = [root]
  WHILE queue IS NOT EMPTY
    level = []
    FOR i FROM 0 TO LENGTH(queue) - 1
      node = DEQUEUE(queue)
      level += [node.value]
      IF node.left IS NOT NULL THEN
        ENQUEUE(queue, node.left)
      END IF
      IF node.right IS NOT NULL THEN
        ENQUEUE(queue, node.right)
      END IF
    END FOR
    result += [level]
  END WHILE
  RETURN result
END FUNCTION
'''


def _compile(source=source_e_26):
    result = GenericPseudocodeProcessor().process(source)
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    flow = FlowDiagramEncoder().encode(parsed.ast)
    compiled = AJPythonCompiler().compile(flow)
    namespace = {}
    exec(compiled.source_code, namespace)
    return result, compiled.source_code, namespace


class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


def test_gc229_recovers_seeded_list_backed_queue_operations():
    result, python_source, namespace = _compile()
    assert any(t.rule == 'GC229' for t in result.transformations)
    assert 'DEQUEUE' not in result.processed_source
    assert 'ENQUEUE' not in result.processed_source
    assert 'REMOVE FIRST ITEM FROM queue' in result.processed_source
    assert 'APPEND node.left TO queue' in result.processed_source
    assert 'APPEND node.right TO queue' in result.processed_source
    assert 'queue.pop(0)' in python_source
    assert 'queue.append(node.left)' in python_source

    root = Node(
        1,
        Node(2, Node(4), Node(5)),
        Node(3, Node(6), Node(7)),
    )
    assert namespace['LEVEL_ORDER_TRAVERSAL'](root) == [[1], [2, 3], [4, 5, 6, 7]]


def test_gc229_handles_irregular_tree_shape():
    _, _, namespace = _compile()
    root = Node(1, None, Node(2, Node(3), None))
    assert namespace['LEVEL_ORDER_TRAVERSAL'](root) == [[1], [2], [3]]


def test_gc229_does_not_treat_plain_seeded_list_as_queue_without_queue_ops():
    source = '''FUNCTION f(root)
  items = [root]
  RETURN items
END FUNCTION
'''
    result = GenericPseudocodeProcessor().process(source)
    assert not any(t.rule == 'GC229' for t in result.transformations)


def test_gc229_does_not_rewrite_queue_ops_for_unproven_receiver():
    source = '''FUNCTION f(queue, value)
  ENQUEUE(queue, value)
  RETURN DEQUEUE(queue)
END FUNCTION
'''
    result = GenericPseudocodeProcessor().process(source)
    assert not any(t.rule == 'GC229' for t in result.transformations)
    assert 'ENQUEUE' in result.processed_source
    assert 'DEQUEUE' in result.processed_source


def test_gc229_does_not_rewrite_operations_for_different_receiver():
    source = '''FUNCTION f(root, other, value)
  queue = [root]
  ENQUEUE(other, value)
  RETURN DEQUEUE(other)
END FUNCTION
'''
    result = GenericPseudocodeProcessor().process(source)
    assert not any(t.rule == 'GC229' for t in result.transformations)
    assert 'ENQUEUE' in result.processed_source
    assert 'DEQUEUE' in result.processed_source
