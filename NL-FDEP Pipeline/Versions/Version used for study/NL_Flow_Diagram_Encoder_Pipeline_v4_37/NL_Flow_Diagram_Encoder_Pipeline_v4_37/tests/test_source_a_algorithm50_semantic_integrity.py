from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _raw_algorithm50():
    return '''BEGIN
    INPUT DroneList
    INPUT Destination

    WHILE Drones have not reached Destination

        FOR EACH Drone
            DETECT nearby obstacles
            DETECT nearby drones

            CALCULATE safe path

            UPDATE Drone position
        ENDFOR

        CHECK for possible collisions

        IF Collision risk detected THEN
            RECALCULATE paths
        ENDIF

    ENDWHILE

    OUTPUT "All drones reached destination safely"
END
'''


def test_source_a_algorithm50_essential_abstractions_remain_expected_failure():
    result = PseudocodeProfileProcessor().process(
        _raw_algorithm50(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )

    processed = result.processed_source
    for required in (
        "INPUT DroneList",
        "INPUT Destination",
        "WHILE Drones have not reached Destination",
        "DETECT nearby obstacles",
        "DETECT nearby drones",
        "CALCULATE safe path",
        "UPDATE Drone position",
        "CHECK for possible collisions",
        "IF Collision risk detected THEN",
        "RECALCULATE paths",
    ):
        assert required in processed

    # Do not disguise the missing semantics with a generated wrapper or helper
    # calls, and do not convert the structured drone input to an interactive
    # string merely to force parsing.
    forbidden = (
        "FUNCTION PROCESS",
        "FUNCTION unnamed_function",
        'DroneList <- INPUT(STRING(',
        "CALL detect",
        "CALL calculate",
        "CALL update",
        "CALL recalculate",
        "safe_path(",
        "collision_risk(",
    )
    for text in forbidden:
        assert text not in processed

    parsed = AJParserFacade().parse(processed)
    assert not parsed.success


def test_source_a_algorithm50_guard_does_not_invent_motion_or_collision_algorithms():
    result = PseudocodeProfileProcessor().process(
        _raw_algorithm50(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    lowered = result.processed_source.lower()
    for forbidden in (
        "a_star",
        "dijkstra",
        "velocity_obstacle",
        "potential_field",
        "pathfinding",
        "avoid_collision",
        "nearest_obstacle",
    ):
        assert forbidden not in lowered
