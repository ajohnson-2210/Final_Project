from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _source_b_algorithm50_source() -> str:
    return '''FUNCTION coordinateDrones(drones, airspace):
    WHILE mission not complete:
        FOR each drone IN drones:
            nextMove ← drone.planNextMove(drone.destination)
            FOR each otherDrone IN drones:
                IF predictedCollision(drone, otherDrone, nextMove) THEN
                    nextMove ← drone.rerouteAround(otherDrone)
            IF nextMove is within airspace bounds THEN
                drone.move(nextMove)
            ELSE
                drone.hover()
            drone.broadcastPosition(drone.currentPosition)
        SYNCHRONISE all drone positions
'''


def test_source_b_algorithm50_remains_expected_failure_without_abstract_reconstruction():
    result = PseudocodeProfileProcessor().process(
        _source_b_algorithm50_source(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    processed = result.processed_source

    # Preserve the supplied abstractions rather than translating them into a
    # conventional coordination/collision-avoidance implementation.
    for required in (
        "mission not complete",
        "predictedCollision(drone, otherDrone, nextMove)",
        "nextMove is within airspace bounds",
        "drone.planNextMove(drone.destination)",
        "drone.rerouteAround(otherDrone)",
        "drone.move(nextMove)",
        "drone.hover()",
        "drone.broadcastPosition(drone.currentPosition)",
        "SYNCHRONISE all drone positions",
    ):
        assert required in processed

    # No inferred completion, bounds, collision, synchronisation or motion
    # solution may be introduced.
    lowered = processed.lower()
    for forbidden in (
        "alldronesreachedtargets",
        "airspace.contains",
        "synchronisepositions",
        "syncpositions",
        "collisiondetection",
        "velocity_obstacle",
        "potential_field",
        "a_star",
        "dijkstra",
        "threading.barrier",
    ):
        assert forbidden not in lowered

    assert not AJParserFacade().parse(processed).success


def test_source_b_algorithm50_free_collision_helper_is_not_silently_bound():
    result = PseudocodeProfileProcessor().process(
        _source_b_algorithm50_source(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    # The compatibility layer must not turn an undefined dependency into an
    # apparently bound helper merely to make the algorithm parse.
    assert "FUNCTION predictedCollision" not in result.processed_source
    assert "IMPORT predictedCollision" not in result.processed_source
