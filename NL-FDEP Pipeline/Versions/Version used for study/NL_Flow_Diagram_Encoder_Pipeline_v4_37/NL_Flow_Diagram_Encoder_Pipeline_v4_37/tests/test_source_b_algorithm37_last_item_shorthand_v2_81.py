import unittest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_b_ALGORITHM_37 = '''FUNCTION Stack():
    data ← []
    
    FUNCTION push(item):
        APPEND item TO data
    
    FUNCTION pop():
        IF data is empty THEN RETURN "Underflow"
        REMOVE and RETURN last item of data
    
    FUNCTION peek():
        IF data is empty THEN RETURN "Empty"
        RETURN last item of data
'''


class source_bAlgorithm37LastItemShorthandTests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()
        self.parser = AJParserFacade()

    def process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def compile_processed(self, source):
        processed = self.process(source)
        parsed = self.parser.parse(processed.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        self.assertTrue(compiled.success)
        return processed, compiled.source_code

    def test_exact_source_b37_recovers_only_explicit_last_item_operations(self):
        processed, python_source = self.compile_processed(source_b_ALGORITHM_37)

        self.assertIn("RETURN REMOVE LAST ITEM FROM THIS.data", processed.processed_source)
        self.assertIn("RETURN THIS.data[-1]", processed.processed_source)
        self.assertTrue(any(t.rule == "GC139" for t in processed.transformations))

        # v2.82 adds a separate, evidence-backed GC196 recovery for the
        # outer stateful ADT container.  This v2.81 regression remains focused
        # on GC139's last-item semantics and must remain valid after that later
        # structural recovery.
        self.assertIn("return self.data.pop(-1)", python_source)
        self.assertIn("return self.data[(-1)]", python_source)

    def test_general_list_backed_variable_uses_same_destructive_return_rule(self):
        source = '''FUNCTION takeLast ACCEPTS(items AS LIST)
    REMOVE and RETURN last item of items
ENDFUNCTION
'''
        processed, python_source = self.compile_processed(source)
        self.assertIn("RETURN REMOVE LAST ITEM FROM items", processed.processed_source)
        self.assertIn("return items.pop(-1)", python_source)

        namespace = {}
        exec(python_source, namespace)
        values = [3, 5, 8]
        self.assertEqual(8, namespace["takeLast"](values))
        self.assertEqual([3, 5], values)

    def test_general_list_backed_variable_uses_same_non_destructive_read_rule(self):
        source = '''FUNCTION peekLast ACCEPTS(items AS LIST)
    RETURN last item of items
ENDFUNCTION
'''
        processed, python_source = self.compile_processed(source)
        self.assertIn("RETURN items[-1]", processed.processed_source)
        self.assertIn("return items[(-1)]", python_source)

        namespace = {}
        exec(python_source, namespace)
        values = [3, 5, 8]
        self.assertEqual(8, namespace["peekLast"](values))
        self.assertEqual([3, 5, 8], values)

    def test_undeclared_collection_does_not_trigger_last_item_recovery(self):
        source = '''FUNCTION ambiguous ACCEPTS()
    REMOVE and RETURN last item of items
ENDFUNCTION
'''
        processed = self.process(source)
        self.assertIn("REMOVE and RETURN last item of items", processed.processed_source)
        self.assertFalse(any(t.rule == "GC139" for t in processed.transformations))
        parsed = self.parser.parse(processed.processed_source)
        self.assertFalse(parsed.success)

    def test_set_backing_does_not_trigger_ordered_last_item_recovery(self):
        source = '''FUNCTION ambiguous ACCEPTS()
    items <- EMPTY SET
    RETURN last item of items
ENDFUNCTION
'''
        processed = self.process(source)
        self.assertIn("RETURN last item of items", processed.processed_source)
        self.assertFalse(any(t.rule == "GC139" for t in processed.transformations))
        parsed = self.parser.parse(processed.processed_source)
        self.assertFalse(parsed.success)


if __name__ == "__main__":
    unittest.main()
