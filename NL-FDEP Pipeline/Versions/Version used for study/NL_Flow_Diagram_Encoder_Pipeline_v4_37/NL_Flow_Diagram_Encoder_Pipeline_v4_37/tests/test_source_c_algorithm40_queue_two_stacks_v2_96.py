import unittest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_c_40_SOURCE = '''CLASS QueueUsingStacks:
    stack1 = empty stack (for enqueue)
    stack2 = empty stack (for dequeue)

    FUNCTION enqueue(item):
        stack1.push(item)

    FUNCTION dequeue():
        IF stack2 IS empty:
            WHILE stack1 IS NOT empty:
                stack2.push(stack1.pop())
        IF stack2 IS empty:
            RETURN NULL // Queue is empty
        RETURN stack2.pop()
'''


class source_cAlgorithm40QueueTwoStacksV296Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()
        self.parser = AJParserFacade()

    def test_exact_motivating_occurrence_normalises_without_reconstruction(self):
        result = self.processor.process(
            source_c_40_SOURCE,
            PseudocodeProfile.GENERIC_COMPATIBILITY,
        )

        self.assertIn("CLASS QueueUsingStacks", result.processed_source)
        self.assertIn("PROPERTY stack1", result.processed_source)
        self.assertIn("PROPERTY stack2", result.processed_source)
        self.assertNotIn("PROPERTY stack1 AS LIST", result.processed_source)
        self.assertNotIn("PROPERTY stack2 AS LIST", result.processed_source)
        self.assertIn("CONSTRUCTOR ACCEPTS()", result.processed_source)
        self.assertIn("PROPERTY THIS.stack1 <- CALL create_stack()", result.processed_source)
        self.assertIn("PROPERTY THIS.stack2 <- CALL create_stack()", result.processed_source)
        self.assertIn("METHOD enqueue ACCEPTS(item)", result.processed_source)
        self.assertIn("CALL PUSH(item, THIS.stack1)", result.processed_source)
        self.assertIn(
            "CALL PUSH(CALL POP(THIS.stack1), THIS.stack2)",
            result.processed_source,
        )
        self.assertIn("IF CALL stack_is_empty(THIS.stack2) THEN", result.processed_source)
        self.assertIn("WHILE NOT CALL stack_is_empty(THIS.stack1) DO", result.processed_source)
        self.assertIn("RETURN CALL POP(THIS.stack2)", result.processed_source)
        self.assertTrue(result.processed_source.rstrip().endswith("ENDCLASS"))

        rules = [item.rule for item in result.transformations]
        self.assertIn("GC202", rules)
        self.assertIn("GC203", rules)

        parsed = self.parser.parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        self.assertTrue(compiled.success)

        namespace = {}
        exec(compiled.source_code, namespace)
        queue = namespace["QueueUsingStacks"]()
        queue.enqueue("A")
        queue.enqueue("B")
        queue.enqueue("C")
        self.assertEqual("A", queue.dequeue())
        self.assertEqual("B", queue.dequeue())
        queue.enqueue("D")
        self.assertEqual("C", queue.dequeue())
        self.assertEqual("D", queue.dequeue())
        self.assertIsNone(queue.dequeue())


if __name__ == "__main__":
    unittest.main()
