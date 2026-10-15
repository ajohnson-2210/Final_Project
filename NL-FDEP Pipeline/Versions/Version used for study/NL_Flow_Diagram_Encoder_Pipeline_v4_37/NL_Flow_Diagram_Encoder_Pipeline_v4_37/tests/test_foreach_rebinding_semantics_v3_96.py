import unittest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


class ForEachRebindingSemanticsV396Tests(unittest.TestCase):
    def compile_aj(self, source: str) -> str:
        parsed = AJParserFacade().parse(source)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        compiled = AJPythonCompiler().compile(flow)
        self.assertTrue(compiled.success, compiled.message)
        return compiled.source_code

    def test_rebinding_foreach_variable_does_not_write_back_to_collection(self):
        source = """FUNCTION example ACCEPTS(values)
    FOR EACH value IN values DO
        value <- 0
    ENDFOR
    RETURN values
ENDFUNCTION
"""
        python_source = self.compile_aj(source)

        self.assertIn("for value in values:", python_source)
        self.assertNotIn("enumerate(values)", python_source)
        self.assertNotIn("values[_value_index] = value", python_source)

        namespace = {}
        exec(python_source, namespace)
        values = [1, 2, 3]
        result = namespace["example"](values)
        self.assertEqual(result, [1, 2, 3])
        self.assertEqual(values, [1, 2, 3])

    def test_source_reverse_row_is_explicit_in_place_mutation(self):
        source = """FUNCTION rotate_rows ACCEPTS(Matrix)
    FOR EACH Row IN Matrix DO
        REVERSE Row
    ENDFOR
    RETURN Matrix
ENDFUNCTION
"""
        normalized = PseudocodeProfileProcessor().process(
            source, PseudocodeProfile.GENERIC_COMPATIBILITY
        )
        self.assertIn("CALL reverse_list(Row)", normalized.processed_source)
        self.assertNotIn("Row <- CALL reverse_value(Row)", normalized.processed_source)

        python_source = self.compile_aj(normalized.processed_source)
        self.assertIn("for Row in Matrix:", python_source)
        self.assertIn("Row.reverse()", python_source)
        self.assertNotIn("enumerate(Matrix)", python_source)

        namespace = {}
        exec(python_source, namespace)
        matrix = [[1, 2], [3, 4]]
        result = namespace["rotate_rows"](matrix)
        self.assertEqual(result, [[2, 1], [4, 3]])
        self.assertEqual(matrix, [[2, 1], [4, 3]])


if __name__ == "__main__":
    unittest.main()
