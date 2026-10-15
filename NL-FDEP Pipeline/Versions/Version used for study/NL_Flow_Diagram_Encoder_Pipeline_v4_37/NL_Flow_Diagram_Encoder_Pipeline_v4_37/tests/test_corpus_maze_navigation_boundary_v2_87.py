"""Empirical cross-corpus evidence for one shared maze semantic boundary.

These snippets retain the distinct surface forms observed in the study outputs.
They are evidence for a corpus-wide rule; implementation logic must not inspect
model names, filenames, algorithm numbers, or wrapper/function names.
"""

from pseudocode_profiles import PseudocodeProfileProcessor


def _guard(source):
    return (
        PseudocodeProfileProcessor()
        .generic_processor.obvious_mismatch_normaliser
        ._has_abstract_maze_navigation_semantics(source)
    )


def test_source_a_descriptive_neighbour_relation_hits_shared_boundary():
    assert _guard('''INPUT Maze
FOR EACH Neighbour of Current
    IF Neighbour not visited THEN
        ENQUEUE Neighbour
    ENDIF
ENDFOR
''')


def test_source_b_descriptive_coordinate_neighbour_relation_hits_shared_boundary():
    assert _guard('''FUNCTION solveMaze(maze, start, end):
FOR each neighbour OF current (up/down/left/right):
    IF neighbour is valid AND not a wall AND not visited THEN
        ADD neighbour TO visited
''')


def test_source_c_descriptive_bounds_and_blocked_cell_hits_shared_boundary():
    assert _guard('''FUNCTION findPath(maze, start, end):
IF newRow, newCol are within bounds AND maze[newRow][newCol] is not blocked AND visited[newRow][newCol] == False:
    visited[newRow][newCol] = True
''')


def test_source_e_descriptive_wall_predicate_hits_shared_boundary():
    assert _guard('''FUNCTION PATHFINDING(maze, start, end)
FOR cell IN maze
    IF cell IS NOT A WALL THEN
        graph += [cell]
    END IF
END FOR
''')


def test_source_d_undefined_free_get_valid_neighbors_hits_shared_boundary():
    assert _guard('''FUNCTION SolveMaze(maze, start, end):
FOR EACH neighbor IN GetValidNeighbors(maze, curr) DO
    IF neighbor NOT IN visited THEN
        ADD neighbor TO visited
    END IF
END FOR
''')


def test_source_f_undefined_free_get_valid_neighbors_hits_shared_boundary():
    assert _guard('''INPUT maze, start, end
FOR neighbor in getValidNeighbors(curr, maze):
    IF neighbor not in visited:
        visited.add(neighbor)
''')
