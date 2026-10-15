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