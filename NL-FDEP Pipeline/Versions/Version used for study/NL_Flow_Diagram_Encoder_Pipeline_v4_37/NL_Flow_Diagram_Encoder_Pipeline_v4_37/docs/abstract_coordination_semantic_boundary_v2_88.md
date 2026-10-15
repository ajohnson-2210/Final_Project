# Abstract coordination/control semantic boundary — v2.88

## Rule

A compatibility normaliser must not convert descriptive coordination, collision-avoidance, completion, proximity, bounds, path-planning, or synchronisation language into an executable solution merely because a conventional implementation is familiar.

The boundary is corpus-wide and source-shape independent. It does not inspect model names, filenames, algorithm numbers, prompt labels, wrapper names, or particular function names.

## Descriptive semantics that remain unresolved

Examples include:

```text
WHILE mission not complete
WHILE Drones have not reached Destination
nextMove is within airspace bounds
drone IS NEAR OBSTACLE
Collision risk detected
DETECT nearby drones
CALCULATE safe path
CHECK for possible collisions
SYNCHRONISE all drone positions
```

Those phrases do not establish the executable predicate, geometry representation, proximity metric, collision model, planning algorithm, barrier/synchronisation mechanism, or state transition required for execution.

The compatibility layer therefore preserves the unresolved text and allows strict AJ parsing to fail rather than selecting an implementation.

## Free helper dependencies

In this coordination semantic family, a Python-like free helper call that would need compatibility conversion is executable only when its binding is supplied by the source or it is a recognised AJ/Python intrinsic.

Examples of unbound study-output helpers include:

```text
predictedCollision(...)
allDronesReachedTargets()
computeAStar(...)
resolveConflicts(...)
syncPositions()
distance(...)
calculateSafeVelocity(...)
CalculateTargetVector(...)
Distance(...)
Direction(...)
LimitSpeed(...)
ADJUST_TRAJECTORY(...)
```

The compatibility layer must not invent definitions, imports, or substitute implementations for such routines.

Valid dependency evidence includes an explicit local definition or an explicit import/binding of the exact free helper. Explicit AJ v1.1 member calls are different because the source itself names an object interface, for example:

```text
mission.isComplete()
airspace.contains(nextMove)
drone.planNextMove(drone.destination)
drone.move(nextMove)
drone.hover()
drone.broadcastPosition(drone.currentPosition)
```

These member calls are preserved; the compatibility layer does not invent their method names or object bindings.

## Empirical corpus evidence

Algorithm 50 study outputs express the same semantic gap through different surface forms:

- source_a: descriptive completion, detection, path calculation, collision checking and recalculation stages;
- source_b: `mission not complete`, an unbound `predictedCollision(...)`, descriptive airspace bounds and `SYNCHRONISE all drone positions`;
- source_e: descriptive `IS NEAR` predicates and unbound `ADJUST_TRAJECTORY(...)`;
- source_f: unbound free path-planning/conflict/synchronisation helpers;
- source_c: unbound distance and safe-velocity helpers within otherwise explicit object-state updates;
- source_d: unbound vector/geometry/limit helpers within otherwise explicit object member updates.

These are evidence for one shared rule. No implementation branch depends on the source model or corpus file.

## Recovery boundary

Permitted:

- preserve explicit loops, assignments, comparisons and object member calls;
- normalise syntax that is structurally unambiguous;
- preserve an explicitly defined/imported free helper call without inventing its body.

Not permitted:

- create a mission-completion predicate;
- choose an airspace coordinate/bounds representation;
- choose a proximity or collision-detection model;
- select A*, Dijkstra, velocity-obstacle, potential-field, priority, or other planning/avoidance algorithms;
- create missing helper definitions/imports;
- choose a synchronisation/barrier mechanism;
- infer missing state transitions merely to obtain executable Python.

## Dialect status

AJ_24038155 Dialect v1.1 remains frozen and unchanged. v2.88 is a compatibility-pipeline semantic-integrity correction only.
