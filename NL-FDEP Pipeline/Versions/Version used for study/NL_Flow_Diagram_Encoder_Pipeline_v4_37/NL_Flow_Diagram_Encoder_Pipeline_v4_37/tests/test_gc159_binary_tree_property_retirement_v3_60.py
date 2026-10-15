import unittest

from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


class GC159BinaryTreePropertyRetirementV360Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def test_root_name_does_not_reinterpret_declared_node_value_identifier(self):
        source = """FUNCTION inspect ACCEPTS(root)
    node_value <- 5
    OUTPUT node_value
    RETURN root
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("node_value <- 5", result.processed_source)
        self.assertIn("OUTPUT node_value", result.processed_source)
        self.assertNotIn("node.value", result.processed_source)
        self.assertFalse(any(t.rule == "GC159" for t in result.transformations))

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_root_name_does_not_reinterpret_node_left_identifier(self):
        source = """FUNCTION inspect ACCEPTS(root)
    node_left <- root
    RETURN node_left
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("node_left <- root", result.processed_source)
        self.assertIn("RETURN node_left", result.processed_source)
        self.assertNotIn("node.left", result.processed_source)
        self.assertFalse(any(t.rule == "GC159" for t in result.transformations))

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_explicit_node_member_access_is_preserved(self):
        source = """FUNCTION inspect ACCEPTS(root, node)
    OUTPUT node.value
    RETURN root
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("OUTPUT node.value", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_specialised_level_order_flattened_names_are_no_longer_repaired(self):
        source = """FUNCTION LEVEL_ORDER_TRAVERSAL ACCEPTS(root)
    queue <- LIST [root]
    node <- CALL DEQUEUE(queue)
    OUTPUT node_value
    IF node_left != NONE THEN
        OUTPUT node_left
    ENDIF
    IF node_right != NONE THEN
        OUTPUT node_right
    ENDIF
    RETURN root
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("OUTPUT node_value", result.processed_source)
        self.assertIn("node_left != NONE", result.processed_source)
        self.assertIn("OUTPUT node_left", result.processed_source)
        self.assertIn("node_right != NONE", result.processed_source)
        self.assertIn("OUTPUT node_right", result.processed_source)
        self.assertFalse(any(t.rule == "GC159" for t in result.transformations))

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)
        self.assertIn("node_value", str(parsed.error))

    def test_level_order_like_name_without_specialised_gate_preserves_identifier(self):
        source = """FUNCTION breadthLevels ACCEPTS(root)
    node_value <- 1
    OUTPUT node_value
    RETURN root
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("node_value <- 1", result.processed_source)
        self.assertNotIn("node.value", result.processed_source)
        self.assertFalse(any(t.rule == "GC159" for t in result.transformations))


if __name__ == "__main__":
    unittest.main()
