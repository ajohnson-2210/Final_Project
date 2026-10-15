INPUT maze, start, end

queue <- [(start, [start])]
visited <- {start}

WHILE queue not empty:
    curr, path = queue.popFront()

    IF curr == end:
        RETURN path

    FOR neighbor in getValidNeighbors(curr, maze):
        IF neighbor not in visited:
            visited.add(neighbor)
            queue.__reserved_keyword__append((neighbor, path + [neighbor]))

RETURN "No Path"