import unittest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import GenericPseudocodeProcessor


SOURCE = """BEGIN
    CREATE Stack1
    CREATE Stack2

    ENQUEUE(Item)
        PUSH Item onto Stack1

    DEQUEUE()
        IF Stack2 is empty THEN
            WHILE Stack1 is not empty
                PUSH POP(Stack1) onto Stack2
            ENDWHILE
        ENDIF

        OUTPUT POP(Stack2)
END
"""


class GC124AbstractStackPreservationTests(unittest.TestCase):
    def process(self, source=SOURCE):
        return GenericPseudocodeProcessor().process(source)

    def test_gc124_preserves_stack_abstraction_in_canonical_source(self):
        result = self.process()
        canonical = result.processed_source
        self.assertIn("Stack1 <- CALL create_stack()", canonical)
        self.assertIn("Stack2 <- CALL create_stack()", canonical)
        self.assertIn("IF CALL stack_is_empty(Stack2) THEN", canonical)
        self.assertIn("WHILE NOT CALL stack_is_empty(Stack1) DO", canonical)
        self.assertIn("CALL PUSH(CALL POP(Stack1), Stack2)", canonical)
        self.assertNotIn("Stack1 <- EMPTY LIST", canonical)
        self.assertNotIn("Stack2 <- EMPTY LIST", canonical)

    def test_gc124_canonical_source_parses(self):
        result = self.process()
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_gc124_compiler_lowers_explicit_stack_abstraction_to_python_list(self):
        result = self.process()
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow).source_code
        self.assertIn("Stack1 = []", compiled)
        self.assertIn("Stack2 = []", compiled)
        self.assertIn("Stack1.append(Item)", compiled)
        self.assertIn("len(Stack2) == 0", compiled)
        self.assertIn("len(Stack1) == 0", compiled)
        self.assertIn("temp = Stack1.pop(-1)", compiled)
        self.assertIn("Stack2.append(temp)", compiled)
        self.assertIn("print(Stack2.pop(-1))", compiled)

    def test_explicit_empty_list_source_remains_explicit_list_data(self):
        source = """Stack1 <- EMPTY LIST
CALL PUSH(1, Stack1)
OUTPUT CALL POP(Stack1)
"""
        parsed = AJParserFacade().parse(source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow).source_code
        self.assertIn("Stack1 = []", compiled)
        self.assertIn("Stack1.append(1)", compiled)
        self.assertIn("print(Stack1.pop(-1))", compiled)


if __name__ == "__main__":
    unittest.main()
