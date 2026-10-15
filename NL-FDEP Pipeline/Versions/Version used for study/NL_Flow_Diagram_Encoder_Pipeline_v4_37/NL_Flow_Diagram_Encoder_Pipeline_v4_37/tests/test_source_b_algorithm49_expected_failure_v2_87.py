from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_b_49 = '''FUNCTION solveMaze(maze, start, end):
    queue ← [(start, [start])]
    visited ← {start}
    WHILE queue is not empty:
        (current, path) ← DEQUEUE from queue
        IF current == end THEN RETURN path
        FOR each neighbour OF current (up/down/left/right):
            IF neighbour is valid AND not a wall AND not visited THEN
                ADD neighbour TO visited
                ENQUEUE (neighbour, path + [neighbour]) TO queue
    RETURN "No path found"
'''


def _process(source=source_b_49):
    return PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )


def test_source_b_algorithm49_remains_expected_failure_without_maze_semantics():
    result = _process()

    assert "neighbour OF current (up/down/left/right)" in result.processed_source
    assert "neighbour is valid AND not a wall" in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success


def test_source_b_algorithm49_does_not_invent_coordinate_or_traversability_solution():
    result = _process()
    lowered = result.processed_source.lower()

    for forbidden in (
        "tuple(row - 1, col)",
        "tuple(row + 1, col)",
        "tuple(row, col - 1)",
        "tuple(row, col + 1)",
        "is_traversable",
        "neighbourrow >= 0",
        "neighbourcol >= 0",
    ):
        assert forbidden not in lowered

    assert all(t.rule != "GC147" for t in result.transformations)
