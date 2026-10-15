from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _raw_algorithm49():
    return '''BEGIN
    INPUT Maze
    INPUT Start, Goal

    CREATE Queue
    MARK Start as visited
    ENQUEUE Start

    WHILE Queue is not empty
        Current <- DEQUEUE Queue

        IF Current = Goal THEN
            OUTPUT "Path Found"
            STOP
        ENDIF

        FOR EACH Neighbour of Current
            IF Neighbour not visited THEN
                MARK Neighbour as visited
                ENQUEUE Neighbour
            ENDIF
        ENDFOR
    ENDWHILE

    OUTPUT "No Path Found"
END
'''


def test_source_a_algorithm49_undefined_neighbour_relation_remains_expected_failure():
    result = PseudocodeProfileProcessor().process(
        _raw_algorithm49(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )

    # Preserve the model's unresolved neighbour relation. Do not hide its
    # missing semantics behind an assumed adjacency-list representation or an
    # invented helper/wrapper.
    assert "FOR EACH Neighbour of Current" in result.processed_source
    assert "Maze[Current]" not in result.processed_source
    assert "CALL neighbours" not in result.processed_source
    assert "FUNCTION find_path" not in result.processed_source
    assert "random_graph" not in result.processed_source
    assert all(t.rule != "GC128" for t in result.transformations)

    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success


def test_source_a_algorithm49_does_not_invent_graph_or_path_runtime_state():
    result = PseudocodeProfileProcessor().process(
        _raw_algorithm49(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    lowered = result.processed_source.lower()
    for forbidden in (
        "random_graph",
        "maze[current]",
        "neighbours(current)",
        "previous <-",
        "path <-",
        "walk <-",
    ):
        assert forbidden not in lowered
