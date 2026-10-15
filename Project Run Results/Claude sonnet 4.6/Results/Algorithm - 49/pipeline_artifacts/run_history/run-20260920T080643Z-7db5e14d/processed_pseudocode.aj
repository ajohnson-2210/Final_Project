FUNCTION solveMaze(maze, start, end):
    queue <- [(start, [start])]
    visited <- {start}
    WHILE queue is not empty:
        (current, path) <- DEQUEUE from queue
        IF current == end THEN RETURN path
        FOR each neighbour OF current (up/down/left/right):
            IF neighbour is valid AND not a wall AND not visited THEN
                ADD neighbour TO visited
                ENQUEUE (neighbour, path + [neighbour]) TO queue
    RETURN "No path found"