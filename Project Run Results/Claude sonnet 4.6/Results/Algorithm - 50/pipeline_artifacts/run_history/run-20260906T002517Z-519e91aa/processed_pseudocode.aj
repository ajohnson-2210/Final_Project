FUNCTION coordinateDrones(drones, airspace):
    WHILE mission not complete:
        FOR each drone IN drones:
            nextMove <- drone.planNextMove(drone.destination)
            FOR each otherDrone IN drones:
                IF predictedCollision(drone, otherDrone, nextMove) THEN
                    nextMove <- drone.rerouteAround(otherDrone)
            IF nextMove is within airspace bounds THEN
                drone.move(nextMove)
            ELSE
                drone.hover()
            drone.broadcastPosition(drone.currentPosition)
        SYNCHRONISE all drone positions