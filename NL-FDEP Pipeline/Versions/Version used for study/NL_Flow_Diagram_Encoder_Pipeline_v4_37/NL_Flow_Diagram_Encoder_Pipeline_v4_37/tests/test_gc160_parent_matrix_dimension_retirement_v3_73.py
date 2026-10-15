import unittest

from aj_parser import AJParserFacade
from flow_diagram import FlowDiagramEncoder
from aj_python_compiler import AJPythonCompiler
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


class GC160ParentMatrixDimensionRetirementV373Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def _process(self, source):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def _compile(self, canonical):
        parsed = AJParserFacade().parse(canonical)
        self.assertTrue(parsed.success, parsed.error)
        flow = FlowDiagramEncoder().encode(parsed.ast)
        return AJPythonCompiler().compile(flow).source_code

    def test_parent_previous_cell_declaration_does_not_invent_maze_dimensions(self):
        source = """FUNCTION inspect ACCEPTS(maze)
    parent <- 2D array to store previous cell for reconstruction
    RETURN parent
ENDFUNCTION
"""
        result = self._process(source)
        self.assertIn(
            "parent <- 2D array to store previous cell for reconstruction",
            result.processed_source,
        )
        self.assertNotIn("create_matrix(LENGTH OF maze", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)
        self.assertIsNone(parsed.ast)

    def test_explicit_same_size_visited_matrix_keeps_maze_dimensions(self):
        source = """FUNCTION inspect ACCEPTS(maze)
    visited <- 2D boolean array same size as maze initialized to BOOLEAN(False)
    RETURN visited
ENDFUNCTION
"""
        result = self._process(source)
        self.assertIn(
            "visited <- CALL create_matrix(LENGTH OF maze, LENGTH OF maze[0], BOOLEAN(False))",
            result.processed_source,
        )
        python = self._compile(result.processed_source)
        self.assertIn(
            "visited = [[False for _ in range(len(maze[0]))] for _ in range(len(maze))]",
            python,
        )

    def test_source_c_maze_parent_surface_remains_unresolved(self):
        source = """FUNCTION findPath ACCEPTS(maze, start, end)
    queue <- EMPTY LIST
    visited <- 2D boolean array same size as maze initialized to BOOLEAN(False)
    parent <- 2D array to store previous cell for reconstruction
    APPEND start TO queue
    RETURN parent
ENDFUNCTION
"""
        result = self._process(source)
        self.assertIn(
            "parent <- 2D array to store previous cell for reconstruction",
            result.processed_source,
        )
        self.assertIn("visited <- CALL create_matrix(LENGTH OF maze", result.processed_source)
        self.assertNotIn("parent <- CALL create_matrix", result.processed_source)
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)


if __name__ == "__main__":
    unittest.main()
