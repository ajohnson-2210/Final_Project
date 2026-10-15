import unittest

from aj_parser import AJParserFacade
from flow_diagram import FlowDiagramEncoder
from aj_python_compiler import AJPythonCompiler
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


class GC160UninitialisedMatrixNoneFillV370Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def _process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def _compile(self, canonical):
        parsed = AJParserFacade().parse(canonical)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        return AJPythonCompiler().compile(flow).source_code

    def test_uninitialised_rectangular_matrix_uses_none_fill(self):
        source = """FUNCTION addMatrices ACCEPTS(A, B, rows, cols)
    result <- matrix of size rows x cols
    FOR i <- IN RANGE 0 TO rows DO
        FOR j <- IN RANGE 0 TO cols DO
            result[i][j] <- A[i][j] + B[i][j]
        ENDFOR
    ENDFOR
    RETURN result
ENDFUNCTION
"""
        result = self._process(source)
        self.assertIn("result <- CALL create_matrix(rows, cols, NONE)", result.processed_source)
        self.assertNotIn("create_matrix(rows, cols, 0)", result.processed_source)
        python = self._compile(result.processed_source)
        self.assertIn("result = [[None for _ in range(cols)] for _ in range(rows)]", python)

    def test_explicit_zero_fill_remains_zero(self):
        source = """FUNCTION multiplyMatrices ACCEPTS(A, B, rows, cols)
    result <- matrix of size rows x cols initialized with 0
    RETURN result
ENDFUNCTION
"""
        result = self._process(source)
        self.assertIn("result <- CALL create_matrix(rows, cols, 0)", result.processed_source)
        python = self._compile(result.processed_source)
        self.assertIn("result = [[0 for _ in range(cols)] for _ in range(rows)]", python)


if __name__ == "__main__":
    unittest.main()
