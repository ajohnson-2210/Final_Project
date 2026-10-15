import unittest

from aj_parser import AJParserFacade
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor
from aj_python_compiler import AJPythonCompiler


class GC159LevelOrderPropertyRetirementV365Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def test_declared_node_value_stays_identifier_inside_level_order(self):
        source = '''FUNCTION LEVEL_ORDER_TRAVERSAL ACCEPTS(root)
    queue <- LIST [root]
    node <- REMOVE FIRST ITEM FROM queue
    node_value <- 5
    OUTPUT node_value
    RETURN root
ENDFUNCTION
'''
        result = self.process(source)
        self.assertIn('node_value <- 5', result.processed_source)
        self.assertIn('OUTPUT node_value', result.processed_source)
        self.assertNotIn('node.value', result.processed_source)
        self.assertFalse(any(t.rule == 'GC159' for t in result.transformations))

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn('node_value = 5', compiled.source_code)
        self.assertIn('print(node_value)', compiled.source_code)

    def test_declared_node_left_and_right_stay_identifiers(self):
        source = '''FUNCTION LEVEL_ORDER_TRAVERSAL ACCEPTS(root)
    queue <- LIST [root]
    node <- REMOVE FIRST ITEM FROM queue
    node_left <- root
    node_right <- root
    OUTPUT node_left
    OUTPUT node_right
    RETURN root
ENDFUNCTION
'''
        result = self.process(source)
        self.assertIn('node_left <- root', result.processed_source)
        self.assertIn('node_right <- root', result.processed_source)
        self.assertNotIn('node.left', result.processed_source)
        self.assertNotIn('node.right', result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_explicit_node_members_remain_members(self):
        source = '''FUNCTION LEVEL_ORDER_TRAVERSAL ACCEPTS(root)
    queue <- LIST [root]
    node <- REMOVE FIRST ITEM FROM queue
    OUTPUT node.value
    IF node.left != NONE THEN
        APPEND node.left TO queue
    ENDIF
    IF node.right != NONE THEN
        APPEND node.right TO queue
    ENDIF
    RETURN root
ENDFUNCTION
'''
        result = self.process(source)
        self.assertIn('OUTPUT node.value', result.processed_source)
        self.assertIn('node.left != NONE', result.processed_source)
        self.assertIn('APPEND node.left TO queue', result.processed_source)
        self.assertIn('node.right != NONE', result.processed_source)
        self.assertIn('APPEND node.right TO queue', result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn('print(node.value)', compiled.source_code)
        self.assertIn('queue.append(node.left)', compiled.source_code)
        self.assertIn('queue.append(node.right)', compiled.source_code)

    def test_undeclared_flattened_names_are_not_repaired(self):
        source = '''FUNCTION LEVEL_ORDER_TRAVERSAL ACCEPTS(root)
    queue <- LIST [root]
    node <- REMOVE FIRST ITEM FROM queue
    OUTPUT node_value
    RETURN root
ENDFUNCTION
'''
        result = self.process(source)
        self.assertIn('OUTPUT node_value', result.processed_source)
        self.assertNotIn('node.value', result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)
        self.assertIn('node_value', str(parsed.error))


if __name__ == '__main__':
    unittest.main()
