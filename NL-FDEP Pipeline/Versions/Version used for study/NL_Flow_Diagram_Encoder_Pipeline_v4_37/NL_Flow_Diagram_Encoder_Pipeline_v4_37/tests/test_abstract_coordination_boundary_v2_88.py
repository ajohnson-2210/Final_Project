import pytest

from aj_parser import AJParserFacade
from pseudocode_profiles import GenericObviousMismatchNormaliser


@pytest.mark.parametrize(
    "source",
    [
        # source_a study surface: descriptive completion and imperative stages.
        '''BEGIN
INPUT DroneList
INPUT Destination
WHILE Drones have not reached Destination
    FOR EACH Drone
        DETECT nearby obstacles
        CALCULATE safe path
        UPDATE Drone position
    ENDFOR
    CHECK for possible collisions
    IF Collision risk detected THEN
        RECALCULATE paths
    ENDIF
ENDWHILE
END
''',
        # source_b study surface: descriptive completion/bounds/synchronisation
        # plus an unbound free collision helper.
        '''FUNCTION coordinateDrones(drones, airspace):
WHILE mission not complete:
    FOR each drone IN drones:
        nextMove = drone.planNextMove(drone.destination)
        IF predictedCollision(drone, drone, nextMove) THEN
            nextMove = drone.rerouteAround(drone)
        IF nextMove is within airspace bounds THEN
            drone.move(nextMove)
    SYNCHRONISE all drone positions
''',
        # source_e study surface: descriptive proximity predicates and unbound
        # trajectory routine.
        '''FUNCTION COORDINATE_DRONES(drones, obstacles)
FOR drone IN drones
    IF drone IS NEAR OBSTACLE THEN
        ADJUST_TRAJECTORY(drone, obstacles)
    END IF
    IF drone IS NEAR OTHER_DRONE THEN
        ADJUST_TRAJECTORY(drone, other_drone)
    END IF
END FOR
RETURN TRAJECTORIES
END FUNCTION
''',
        # source_f study surface: executable-looking free calls whose bindings are
        # not supplied by the pseudocode.
        '''INPUT drones, targets, safetyRadius
WHILE not allDronesReachedTargets():
    plannedPaths = []
    FOR each drone in drones:
        path = computeAStar(drone.pos, drone.target)
        plannedPaths.append(path)
    adjustedPaths = resolveConflicts(plannedPaths, safetyRadius)
    syncPositions()
RETURN success
''',
        # source_c study surface: explicit object state but undefined distance
        # and velocity-resolution helpers.
        '''FUNCTION updateDronePositions(drones):
FOR each drone in drones:
    proposedPosition = drone.position + drone.velocity
    FOR each otherDrone in drones:
        IF distance(proposedPosition, otherDrone.position) < safeDistance:
            drone.velocity = calculateSafeVelocity(drone.position, otherDrone.position, drone.destination)
RETURN drones
''',
        # source_d study surface: several unbound free vector/geometry helpers.
        '''PROCEDURE CoordinateDroneMovement(drones, safety_radius):
FOR EACH drone IN drones DO
    desired_vector = CalculateTargetVector(drone, drone.destination)
    repulsion_vector = Vector(0, 0, 0)
    FOR EACH other_drone IN drones DO
        dist = Distance(drone.position, other_drone.position)
        IF dist < safety_radius THEN
            repulsion = Direction(other_drone.position -> drone.position) / dist
    drone.setVelocity(LimitSpeed(desired_vector))
END PROCEDURE
''',
    ],
)
def test_coordination_boundary_is_corpus_wide_and_source_shape_independent(source):
    assert GenericObviousMismatchNormaliser._has_abstract_coordination_semantics(source)


def test_undefined_free_branch_helper_is_blocked_even_when_other_semantics_are_explicit():
    source = '''FUNCTION coordinate ACCEPTS(drones, mission, airspace)
    WHILE NOT mission.isComplete() DO
        FOR EACH drone IN drones DO
            nextMove <- drone.planNextMove(drone.destination)
            IF predictedCollision(drone, drone, nextMove) THEN
                drone.hover()
            ELSE IF airspace.contains(nextMove) THEN
                drone.move(nextMove)
            ENDIF
        ENDFOR
    ENDWHILE
ENDFUNCTION
'''
    assert GenericObviousMismatchNormaliser._has_abstract_coordination_semantics(source)


def test_locally_defined_free_helper_is_valid_dependency_evidence():
    source = '''FUNCTION predictedCollision ACCEPTS(first, second, move)
    RETURN BOOLEAN(FALSE)
ENDFUNCTION

FUNCTION coordinate ACCEPTS(drones, mission, airspace)
    WHILE NOT mission.isComplete() DO
        FOR EACH drone IN drones DO
            nextMove <- drone.planNextMove(drone.destination)
            IF CALL predictedCollision(drone, drone, nextMove) THEN
                drone.hover()
            ELSE IF airspace.contains(nextMove) THEN
                drone.move(nextMove)
            ENDIF
        ENDFOR
    ENDWHILE
ENDFUNCTION
'''
    assert not GenericObviousMismatchNormaliser._has_abstract_coordination_semantics(source)
    assert AJParserFacade().parse(source).success


def test_explicit_import_is_valid_free_helper_dependency_evidence_for_boundary():
    source = '''FROM safety_runtime IMPORT predictedCollision
FUNCTION coordinate(drones, mission, airspace):
    WHILE NOT mission.isComplete():
        FOR each drone IN drones:
            nextMove = drone.planNextMove(drone.destination)
            IF predictedCollision(drone, drone, nextMove) THEN
                drone.hover()
            ELSE IF airspace.contains(nextMove) THEN
                drone.move(nextMove)
'''
    # Import syntax is dependency evidence for the compatibility boundary even
    # if the strict AJ parser handles imports elsewhere/not at all.
    assert not GenericObviousMismatchNormaliser._has_abstract_coordination_semantics(source)


def test_explicit_member_interfaces_do_not_trigger_abstract_coordination_guard():
    source = '''FUNCTION coordinate ACCEPTS(drones, mission, airspace)
    WHILE NOT mission.isComplete() DO
        FOR EACH drone IN drones DO
            nextMove <- drone.planNextMove(drone.destination)
            IF airspace.contains(nextMove) THEN
                drone.move(nextMove)
            ELSE
                drone.hover()
            ENDIF
            drone.broadcastPosition(drone.currentPosition)
        ENDFOR
    ENDWHILE
ENDFUNCTION
'''
    assert not GenericObviousMismatchNormaliser._has_abstract_coordination_semantics(source)
    assert AJParserFacade().parse(source).success


def test_unrelated_member_call_algorithm_is_not_caught_by_coordination_boundary():
    source = '''FUNCTION process ACCEPTS(items)
    FOR EACH item IN items DO
        item.update()
    ENDFOR
ENDFUNCTION
'''
    assert not GenericObviousMismatchNormaliser._has_abstract_coordination_semantics(source)
