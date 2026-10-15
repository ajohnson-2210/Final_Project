import unittest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


class GC159MazeCoordinateRetirementV362Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def process(self, source: str):
        return self.processor.process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)

    def test_maze_context_does_not_reinterpret_declared_start_row_identifier(self):
        source = """FUNCTION inspect ACCEPTS(maze, start, end)
    directions <- EMPTY LIST
    start_row <- 5
    OUTPUT start_row
    RETURN start
ENDFUNCTION
"""
        result = self.process(source)

        self.assertIn("start_row <- 5", result.processed_source)
        self.assertIn("OUTPUT start_row", result.processed_source)
        self.assertNotIn("start[0]", result.processed_source)
        self.assertFalse(any(t.rule == "GC159" for t in result.transformations))

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        self.assertIn("start_row = 5", compiled.source_code)
        self.assertIn("print(start_row)", compiled.source_code)

    def test_all_flattened_coordinate_spellings_remain_identifiers(self):
        source = """FUNCTION inspect ACCEPTS(maze, start, end)
    directions <- EMPTY LIST
    start_row <- 0
    start_col <- 1
    current_row <- 2
    current_col <- 3
    direction_row <- 4
    direction_col <- 5
    OUTPUT start_row
    OUTPUT start_col
    OUTPUT current_row
    OUTPUT current_col
    OUTPUT direction_row
    OUTPUT direction_col
    RETURN end
ENDFUNCTION
"""
        result = self.process(source)

        for name in (
            "start_row", "start_col", "current_row", "current_col",
            "direction_row", "direction_col",
        ):
            self.assertIn(name, result.processed_source)
        for invented in (
            "start[0]", "start[1]", "current[0]", "current[1]",
            "direction[0]", "direction[1]",
        ):
            self.assertNotIn(invented, result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)

    def test_explicit_coordinate_indexing_is_preserved(self):
        source = """FUNCTION inspect ACCEPTS(maze, start, end)
    directions <- EMPTY LIST
    start[0] <- 5
    OUTPUT start[0]
    RETURN start
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn("start[0] <- 5", result.processed_source)
        self.assertIn("OUTPUT start[0]", result.processed_source)

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)
        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        self.assertIn("start[0] = 5", compiled.source_code)
        self.assertIn("print(start[0])", compiled.source_code)

    def test_directions_literal_recovery_remains_independent(self):
        source = """FUNCTION inspect ACCEPTS(maze, start, end)
    directions <- [(0,1), (1,0), (0,-1), (-1,0)]
    RETURN directions
ENDFUNCTION
"""
        result = self.process(source)
        self.assertIn(
            "directions <- CALL list_value(TUPLE(0, 1), TUPLE(1, 0), TUPLE(0, -1), TUPLE(-1, 0))",
            result.processed_source,
        )
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)


if __name__ == "__main__":
    unittest.main()
