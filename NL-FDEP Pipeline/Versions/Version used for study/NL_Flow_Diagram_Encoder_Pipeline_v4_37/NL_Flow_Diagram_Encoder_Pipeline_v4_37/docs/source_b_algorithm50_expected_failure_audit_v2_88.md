# source_b Algorithm 50 — expected-failure audit — v2.88

## Source occurrence

```text
FUNCTION coordinateDrones(drones, airspace):
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
```

## Classification

```text
EXPECTED FAIL — ABSTRACT CONTROL PREDICATES / MISSING COORDINATION DEPENDENCIES
```

## Explicitly supplied interface/structure

The source explicitly supplies:

- iteration over drones and other drones;
- `drone.planNextMove(drone.destination)`;
- `drone.rerouteAround(otherDrone)`;
- `drone.move(nextMove)`;
- `drone.hover()`;
- `drone.broadcastPosition(drone.currentPosition)`;
- the branch shape around a collision prediction;
- the branch shape around an airspace-bounds test.

Those object member calls are preserved as source-supplied interfaces under frozen AJ_24038155 Dialect v1.1.

## Missing executable semantics

The source does not define/import:

- the mission-completion predicate represented by `mission not complete`;
- the free routine `predictedCollision(...)`;
- the executable meaning of `nextMove is within airspace bounds`;
- the executable meaning/mechanism of `SYNCHRONISE all drone positions`.

No Python/AJ intrinsic supplies those domain semantics automatically.

## Prohibited reconstruction

The pipeline must not manufacture, select or substitute operations such as:

```text
allDronesReachedTargets(...)
airspace.contains(...)
synchronisePositions(...)
collisionDetection(...)
```

and must not select an avoidance/planning technique such as A*, Dijkstra, velocity obstacles, potential fields, priority arbitration, or a barrier/threading mechanism.

## v2.88 result

The compatibility pipeline stops before generic recovery can convert the unresolved prose or unbound Python-like free call into executable-looking AJ. The source therefore remains a strict parse failure, which is the required outcome for incomplete executable semantics.

The motivating source_b occurrence is retained in `tests/test_source_b_algorithm50_expected_failure_v2_88.py`. The implementation rule itself is exercised separately by corpus-wide and synthetic tests in `tests/test_abstract_coordination_boundary_v2_88.py`.

## Dialect status

AJ_24038155 Dialect v1.1 remains frozen and unchanged.
