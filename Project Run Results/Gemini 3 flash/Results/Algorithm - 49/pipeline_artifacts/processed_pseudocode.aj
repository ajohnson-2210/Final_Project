FUNCTION SolveMaze(maze, start, end):
    queue <- empty Queue
    visited <- empty Set
    parent <- empty Hash Map

    ENQUEUE start TO queue
    ADD start TO visited

    WHILE queue IS NOT EMPTY DO
        curr <- DEQUEUE from queue
        IF curr == end THEN RETURN ReconstructPath(parent, start, end)

        FOR EACH neighbor IN GetValidNeighbors(maze, curr) DO
            IF neighbor NOT IN visited THEN
                ADD neighbor TO visited
                parent[neighbor] <- curr
                ENQUEUE neighbor TO queue
            END IF
        END FOR
    END WHILE

    RETURN "No path found"
END FUNCTION