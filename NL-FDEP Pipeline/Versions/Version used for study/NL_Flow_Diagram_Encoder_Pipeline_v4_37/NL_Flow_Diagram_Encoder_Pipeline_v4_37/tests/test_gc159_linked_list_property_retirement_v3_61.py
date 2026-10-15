import unittest

from aj_parser import AJParserFacade
from flow_diagram import FlowDiagramEncoder
from aj_python_compiler import AJPythonCompiler
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


class GC159LinkedListPropertyRetirementV361Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def test_head_assignment_does_not_reinterpret_declared_current_next_identifier(self):
        source = """FUNCTION inspect ACCEPTS(head)
    current <- head
    current_next <- 5
    OUTPUT current_next
    RETURN head
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("current_next <- 5", result.processed_source)
        self.assertIn("OUTPUT current_next", result.processed_source)
        self.assertNotIn("current.next", result.processed_source)
        self.assertFalse(any(t.rule == "GC159" for t in result.transformations))

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("current_next = 5", compiled.source_code)
        self.assertIn("print(current_next)", compiled.source_code)
        self.assertNotIn("current.next", compiled.source_code)

    def test_explicit_current_member_access_is_preserved(self):
        source = """FUNCTION inspect ACCEPTS(head)
    current <- head
    current.next <- 5
    OUTPUT current.next
    RETURN head
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("current.next <- 5", result.processed_source)
        self.assertIn("OUTPUT current.next", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertIn("current.next = 5", compiled.source_code)
        self.assertIn("print(current.next)", compiled.source_code)

    def test_floyd_flattened_names_are_no_longer_reinterpreted(self):
        source = """FUNCTION hasCycle ACCEPTS(head)
    slow <- head
    fast <- head
    WHILE fast != NONE AND fast_next != NONE DO
        slow <- slow_next
        fast <- fast_next.next
        IF slow == fast THEN
            RETURN BOOLEAN(TRUE)
        ENDIF
    ENDWHILE
    RETURN BOOLEAN(FALSE)
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("fast_next != NONE", result.processed_source)
        self.assertIn("slow <- slow_next", result.processed_source)
        self.assertIn("fast <- fast_next.next", result.processed_source)
        self.assertNotIn("slow <- slow.next", result.processed_source)
        self.assertNotIn("fast <- fast.next.next", result.processed_source)
        self.assertFalse(any(t.rule == "GC159" for t in result.transformations))


if __name__ == "__main__":
    unittest.main()
