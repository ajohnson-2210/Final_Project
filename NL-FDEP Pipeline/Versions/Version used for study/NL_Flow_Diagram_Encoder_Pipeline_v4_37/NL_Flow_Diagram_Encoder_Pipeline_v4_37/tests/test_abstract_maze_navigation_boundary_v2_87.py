from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _normaliser():
    return PseudocodeProfileProcessor().generic_processor.obvious_mismatch_normaliser


def _process(source):
    return PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )


def test_descriptive_neighbour_relation_is_source_shape_independent():
    sources = (
        '''FUNCTION route ACCEPTS(grid, origin)
    FOR EACH adjacentNeighbour OF origin
        OUTPUT adjacentNeighbour
    ENDFOR
ENDFUNCTION
''',
        '''FUNCTION explore ACCEPTS(maze, node)
    FOR each neighbor OF node (left/right)
        OUTPUT neighbor
    ENDFOR
ENDFUNCTION
''',
    )
    for source in sources:
        assert _normaliser()._has_abstract_maze_navigation_semantics(source)


def test_descriptive_bounds_and_wall_predicates_are_not_operationalised():
    source = '''FUNCTION step ACCEPTS(maze, row, col)
    IF row, col are within bounds AND maze[row][col] is not blocked THEN
        RETURN BOOLEAN(True)
    ENDIF
    RETURN BOOLEAN(False)
ENDFUNCTION
'''
    result = _process(source)
    assert "are within bounds" in result.processed_source
    assert "is not blocked" in result.processed_source
    assert "CALL is_traversable" not in result.processed_source
    assert "row >= 0" not in result.processed_source
    assert not AJParserFacade().parse(result.processed_source).success


def test_undefined_free_navigation_helper_is_expected_failure_dependency():
    source = '''FUNCTION route ACCEPTS(maze, current)
    FOR EACH neighbor IN GetValidNeighbors(maze, current) DO
        OUTPUT neighbor
    ENDFOR
ENDFUNCTION
'''
    assert _normaliser()._has_abstract_maze_navigation_semantics(source)


def test_explicitly_defined_navigation_helper_is_allowed():
    source = '''FUNCTION GetValidNeighbors ACCEPTS(maze, current)
    RETURN CALL list_value(current)
ENDFUNCTION

FUNCTION route ACCEPTS(maze, current)
    FOR EACH neighbor IN CALL GetValidNeighbors(maze, current) DO
        IF neighbor == current THEN
            RETURN neighbor
        ENDIF
    ENDFOR
    RETURN NONE
ENDFUNCTION
'''
    assert not _normaliser()._has_abstract_maze_navigation_semantics(source)
    result = _process(source)
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "def GetValidNeighbors(maze, current):" in compiled.source_code
    assert "for neighbor in GetValidNeighbors(maze, current):" in compiled.source_code


def test_explicit_member_navigation_calls_are_allowed_under_frozen_v11():
    source = '''FUNCTION route ACCEPTS(maze, current)
    neighbours <- maze.getValidNeighbors(current)
    FOR EACH neighbour IN neighbours DO
        IF maze.isTraversable(neighbour) THEN
            RETURN neighbour
        ENDIF
    ENDFOR
    RETURN NONE
ENDFUNCTION
'''
    assert not _normaliser()._has_abstract_maze_navigation_semantics(source)
    result = _process(source)
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "maze.getValidNeighbors(current)" in compiled.source_code
    assert "maze.isTraversable(neighbour)" in compiled.source_code


def test_historical_gc128_and_gc147_reconstruction_entry_points_are_removed():
    normaliser = _normaliser()
    assert not hasattr(normaliser, "_normalise_maze_pathfinding")
    assert not hasattr(normaliser, "_normalise_source_b_maze_pathfinding")
