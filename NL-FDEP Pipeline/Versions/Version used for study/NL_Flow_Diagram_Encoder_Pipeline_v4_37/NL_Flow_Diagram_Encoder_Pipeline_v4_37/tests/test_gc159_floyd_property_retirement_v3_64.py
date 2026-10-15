import unittest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


class GC159FloydPropertyRetirementV364Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def compile(self, source):
        result = self.process(source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        self.assertTrue(compiled.success)
        return result, compiled.source_code

    def test_slow_fast_names_do_not_reinterpret_declared_flattened_identifiers(self):
        source = '''FUNCTION inspect ACCEPTS(head)
    slow <- head
    fast <- head
    slow_next <- 5
    fast_next <- 7
    OUTPUT slow_next
    OUTPUT fast_next
    RETURN head
ENDFUNCTION
'''
        result, python = self.compile(source)
        self.assertIn('slow_next <- 5', result.processed_source)
        self.assertIn('fast_next <- 7', result.processed_source)
        self.assertIn('OUTPUT slow_next', result.processed_source)
        self.assertIn('OUTPUT fast_next', result.processed_source)
        self.assertNotIn('slow.next', result.processed_source)
        self.assertNotIn('fast.next', result.processed_source)
        self.assertFalse(any(t.rule == 'GC159' for t in result.transformations))
        self.assertIn('slow_next = 5', python)
        self.assertIn('fast_next = 7', python)
        self.assertIn('print(slow_next)', python)
        self.assertIn('print(fast_next)', python)

    def test_tortoise_hare_names_do_not_reinterpret_declared_flattened_identifiers(self):
        source = '''FUNCTION inspect ACCEPTS(head)
    tortoise <- head
    hare <- head
    tortoise_next <- 5
    hare_next <- 7
    OUTPUT tortoise_next
    OUTPUT hare_next
    RETURN head
ENDFUNCTION
'''
        result, python = self.compile(source)
        self.assertIn('tortoise_next <- 5', result.processed_source)
        self.assertIn('hare_next <- 7', result.processed_source)
        self.assertNotIn('tortoise.next', result.processed_source)
        self.assertNotIn('hare.next', result.processed_source)
        self.assertFalse(any(t.rule == 'GC159' for t in result.transformations))
        self.assertIn('tortoise_next = 5', python)
        self.assertIn('hare_next = 7', python)

    def test_explicit_floyd_member_access_remains_member_access(self):
        source = '''FUNCTION hasCycle ACCEPTS(head)
    slow <- head
    fast <- head
    WHILE fast != NONE AND fast.next != NONE DO
        slow <- slow.next
        fast <- fast.next.next
        IF slow == fast THEN
            RETURN BOOLEAN(TRUE)
        ENDIF
    ENDWHILE
    RETURN BOOLEAN(FALSE)
ENDFUNCTION
'''
        result, python = self.compile(source)
        self.assertIn('fast.next != NONE', result.processed_source)
        self.assertIn('slow <- slow.next', result.processed_source)
        self.assertIn('fast <- fast.next.next', result.processed_source)
        self.assertIn('slow = slow.next', python)
        self.assertIn('fast = fast.next.next', python)

    def test_fast_next_dot_next_is_not_reinterpreted_from_flattened_base(self):
        source = '''FUNCTION inspect ACCEPTS(head)
    slow <- head
    fast <- head
    fast_next <- head
    OUTPUT fast_next.next
    RETURN head
ENDFUNCTION
'''
        result, python = self.compile(source)
        self.assertIn('fast_next <- head', result.processed_source)
        self.assertIn('OUTPUT fast_next.next', result.processed_source)
        self.assertNotIn('OUTPUT fast.next.next', result.processed_source)
        self.assertIn('fast_next = head', python)
        self.assertIn('print(fast_next.next)', python)


if __name__ == '__main__':
    unittest.main()
