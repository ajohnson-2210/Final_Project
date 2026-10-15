    FOR EACH drone IN drones DO
        desired_vector <- CalculateTargetVector(drone, drone.destination)
        repulsion_vector <- Vector(0, 0, 0)

        FOR EACH other_drone IN drones DO
            IF drone.id != other_drone.id THEN
                dist <- Distance(drone.position, other_drone.position)
                IF dist < safety_radius THEN
                    repulsion <- Direction(other_drone.position -> drone.position) / dist
                    repulsion_vector <- repulsion_vector + repulsion
                END IF
            END IF
        END FOR

        adjusted_velocity <- desired_vector + (repulsion_vector * AVOIDANCE_WEIGHT)
        drone.setVelocity(LimitSpeed(adjusted_velocity))
    END FOR
END PROCEDURE