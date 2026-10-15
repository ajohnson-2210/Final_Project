FUNCTION findPath(maze, start, end):
    // BFS traversal
    queue <- empty queue
    visited <- 2D boolean array same size as maze initialized to False
    parent <- 2D array to store previous cell for reconstruction

    queue.enqueue(start)
    visited[start.row][start.col] = True

    directions <- [(0,1), (1,0), (0,-1), (-1,0)]
    // right, down, left, up

    WHILE queue IS NOT empty:
        current <- queue.dequeue()
        IF current == end:
            // Reconstruct path
            path <- empty list
            WHILE current != start:
                path.__reserved_keyword__append(current)
                current <- parent[current.row][current.col]
            path.__reserved_keyword__append(start)
            path.reverse()
            RETURN path
        FOR each direction in directions:
            newRow <- current.row + direction.row
            newCol <- current.col + direction.col
            IF newRow, newCol are within bounds AND maze[newRow][newCol] is not blocked AND visited[newRow][newCol] == False:
                visited[newRow][newCol] = True
                parent[newRow][newCol] = current
                queue.enqueue((newRow, newCol))
    RETURN NULL
    // No path found