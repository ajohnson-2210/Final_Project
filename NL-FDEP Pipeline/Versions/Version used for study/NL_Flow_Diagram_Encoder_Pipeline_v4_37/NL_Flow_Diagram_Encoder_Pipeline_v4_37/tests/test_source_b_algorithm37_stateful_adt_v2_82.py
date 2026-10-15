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


class source_bAlgorithm37StatefulADTRecoveryTests(unittest.TestCase):
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

    def test_exact_source_b37_recovers_stateful_function_container_as_class(self):
        processed, python_source = self.compile_processed(source_b_ALGORITHM_37)

        self.assertIn("CLASS Stack", processed.processed_source)
        self.assertIn("PROPERTY data AS LIST", processed.processed_source)
        self.assertIn("CONSTRUCTOR ACCEPTS()", processed.processed_source)
        self.assertIn("PROPERTY THIS.data <- EMPTY LIST", processed.processed_source)
        self.assertIn("ENDCLASS", processed.processed_source)
        self.assertIn("METHOD push ACCEPTS(item)", processed.processed_source)
        self.assertIn("METHOD pop ACCEPTS()", processed.processed_source)
        self.assertIn("METHOD peek ACCEPTS()", processed.processed_source)
        self.assertTrue(any(t.rule == "GC196" for t in processed.transformations))
        self.assertTrue(any(t.rule == "GC139" for t in processed.transformations))

        self.assertIn("class Stack:", python_source)
        self.assertIn("self.data = []", python_source)
        self.assertIn("def push(self, item):", python_source)
        self.assertIn("def pop(self):", python_source)
        self.assertIn("return self.data.pop(-1)", python_source)
        self.assertIn("def peek(self):", python_source)
        self.assertIn("return self.data[(-1)]", python_source)

        namespace = {}
        exec(python_source, namespace)
        stack = namespace["Stack"]()
        self.assertTrue(callable(stack.push))
        self.assertTrue(callable(stack.pop))
        self.assertTrue(callable(stack.peek))
        stack.push(3)
        stack.push(5)
        self.assertEqual(5, stack.peek())
        self.assertEqual(5, stack.pop())
        self.assertEqual(3, stack.peek())

    def test_general_zero_argument_stateful_container_uses_same_class_recovery(self):
        source = '''FUNCTION Bag():
    items ← []
    FUNCTION add(item):
        APPEND item TO items
    FUNCTION take():
        REMOVE and RETURN last item of items
'''
        processed, python_source = self.compile_processed(source)
        self.assertIn("CLASS Bag", processed.processed_source)
        self.assertIn("PROPERTY items AS LIST", processed.processed_source)
        self.assertIn("CONSTRUCTOR ACCEPTS()", processed.processed_source)
        self.assertIn("METHOD add ACCEPTS(item)", processed.processed_source)
        self.assertIn("METHOD take ACCEPTS()", processed.processed_source)
        self.assertTrue(any(t.rule == "GC196" for t in processed.transformations))
        self.assertIn("class Bag:", python_source)
        self.assertIn("self.items = []", python_source)
        self.assertIn("def add(self, item):", python_source)
        self.assertIn("return self.items.pop(-1)", python_source)

        namespace = {}
        exec(python_source, namespace)
        bag = namespace["Bag"]()
        bag.add("A")
        bag.add("B")
        self.assertEqual("B", bag.take())

    def test_one_nested_function_is_not_enough_to_infer_a_class(self):
        source = '''FUNCTION wrapper():
    data ← []
    FUNCTION helper(item):
        APPEND item TO data
'''
        processed = self.process(source)
        self.assertIn("FUNCTION wrapper ACCEPTS()", processed.processed_source)
        self.assertNotIn("CLASS wrapper", processed.processed_source)
        self.assertFalse(any(t.rule == "GC196" for t in processed.transformations))

    def test_nested_helpers_must_all_reference_shared_state(self):
        source = '''FUNCTION wrapper():
    data ← []
    FUNCTION add(item):
        APPEND item TO data
    FUNCTION unrelated(value):
        RETURN value
'''
        processed = self.process(source)
        self.assertIn("FUNCTION wrapper ACCEPTS()", processed.processed_source)
        self.assertNotIn("CLASS wrapper", processed.processed_source)
        self.assertFalse(any(t.rule == "GC196" for t in processed.transformations))

    def test_outer_return_prevents_class_recovery(self):
        source = '''FUNCTION factory():
    data ← []
    FUNCTION add(item):
        APPEND item TO data
    FUNCTION size():
        RETURN LENGTH OF data
    RETURN data
'''
        processed = self.process(source)
        self.assertIn("FUNCTION factory ACCEPTS()", processed.processed_source)
        self.assertNotIn("CLASS factory", processed.processed_source)
        self.assertFalse(any(t.rule == "GC196" for t in processed.transformations))

    def test_outer_control_flow_prevents_class_recovery(self):
        source = '''FUNCTION wrapper():
    data ← []
    IF LENGTH OF data == 0 THEN
        OUTPUT STRING("empty")
    ENDIF
    FUNCTION add(item):
        APPEND item TO data
    FUNCTION size():
        RETURN LENGTH OF data
'''
        processed = self.process(source)
        self.assertIn("FUNCTION wrapper ACCEPTS()", processed.processed_source)
        self.assertNotIn("CLASS wrapper", processed.processed_source)
        self.assertFalse(any(t.rule == "GC196" for t in processed.transformations))


    def test_read_only_shared_state_helpers_do_not_infer_a_class(self):
        source = '''FUNCTION Formatter():
    prefix <- STRING(">")
    FUNCTION left(value):
        RETURN prefix + value
    FUNCTION right(value):
        RETURN value + prefix
'''
        processed = self.process(source)
        self.assertIn("FUNCTION Formatter ACCEPTS()", processed.processed_source)
        self.assertNotIn("CLASS Formatter", processed.processed_source)
        self.assertFalse(any(t.rule == "GC196" for t in processed.transformations))

    def test_lowercase_stateful_container_name_is_not_enough_for_class_recovery(self):
        source = '''FUNCTION manager():
    items <- EMPTY LIST
    FUNCTION add(item):
        APPEND item TO items
    FUNCTION take():
        RETURN REMOVE LAST ITEM FROM items
'''
        processed = self.process(source)
        self.assertIn("FUNCTION manager ACCEPTS()", processed.processed_source)
        self.assertNotIn("CLASS manager", processed.processed_source)
        self.assertFalse(any(t.rule == "GC196" for t in processed.transformations))


if __name__ == "__main__":
    unittest.main()
