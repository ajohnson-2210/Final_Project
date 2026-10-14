COMMENT import random

OUTPUT STRING("Auto Maze Generator and BFS Solver\n")

FUNCTION shuffle_dirs ACCEPTS(dirs)
    FOR i <- IN RANGE 0 TO LENGTH OF dirs DO
        j <- RANDOM INT(0, (LENGTH OF dirs - 1))
        swap_values <- TUPLE(dirs[j], dirs[i])
        dirs[i] <- swap_values[0]
        dirs[j] <- swap_values[1]
    ENDFOR
ENDFUNCTION

FUNCTION carve_maze ACCEPTS(maze, rows, cols)
    stack <- EMPTY LIST
    r <- 1
    c <- 1
    maze[r][c] <- STRING(" ")
    APPEND TUPLE(r, c) TO stack
    WHILE LENGTH OF stack > 0 DO
        position <- stack[-1]
        r <- position[0]
        c <- position[1]
        dirs <- LIST [TUPLE(0, 2), TUPLE(0, -2), TUPLE(2, 0), TUPLE(-2, 0)]
        CALL shuffle_dirs(dirs)
        carved <- BOOLEAN(FALSE)
        FOR EACH direction IN dirs DO
            dr <- direction[0]
            dc <- direction[1]
            nr <- r + dr
            nc <- c + dc
            IF (1 <= nr AND (nr < (rows - 1))) AND (1 <= nc AND (nc < (cols - 1))) THEN
                IF maze[nr][nc] == STRING("▓") THEN
                    maze[r + (dr INTEGER DIVISION 2)][(c + (dc INTEGER DIVISION 2))] <- STRING(" ")
                    maze[nr][nc] <- STRING(" ")
                    APPEND TUPLE(nr, nc) TO stack
                    carved <- BOOLEAN(TRUE)
                    BREAK
                ENDIF
            ENDIF
        ENDFOR
        IF NOT (carved) THEN
            stack.pop()
        ENDIF
    ENDWHILE
ENDFUNCTION

FUNCTION solve_maze_bfs ACCEPTS(maze, rows, cols)
    start <- NONE
    end <- NONE
    FOR r <- IN RANGE 0 TO rows DO
        FOR c <- IN RANGE 0 TO cols DO
            IF maze[r][c] == STRING("S") THEN
                start <- TUPLE(r, c)
            ELSE IF (maze[r][c] == STRING("E")) THEN
                end <- TUPLE(r, c)
            ENDIF
        ENDFOR
    ENDFOR
    queue <- LIST [start]
    visited <- EMPTY DICTIONARY
    visited[start] <- NONE
    i <- 0
    WHILE i < LENGTH OF queue DO
        queue_position <- queue[i]
        r <- queue_position[0]
        c <- queue_position[1]
        IF TUPLE(r, c) == end THEN
            BREAK
        ENDIF
        FOR EACH direction IN LIST [TUPLE(1, 0), TUPLE(-1, 0), TUPLE(0, 1), TUPLE(0, -1)] DO
            dr <- direction[0]
            dc <- direction[1]
            nr <- r + dr
            nc <- c + dc
            IF 0 <= nr AND nr < rows AND 0 <= nc AND nc < cols THEN
                IF ((maze[nr][nc] != STRING("▓"))) AND ((TUPLE(nr, nc) NOT IN visited)) THEN
                    visited[TUPLE(nr, nc)] <- TUPLE(r, c)
                    APPEND TUPLE(nr, nc) TO queue
                ENDIF
            ENDIF
        ENDFOR
        i <- i + 1
    ENDWHILE
    path <- EMPTY LIST
    node <- end
    WHILE node != NONE DO
        INSERT node INTO path AT 0
        node <- visited.GET(node)
    ENDWHILE
    RETURN path
ENDFUNCTION

FUNCTION mark_path ACCEPTS(maze, path)
    FOR EACH path_cell IN path DO
        r <- path_cell[0]
        c <- path_cell[1]
        IF maze[r][c] NOT IN TUPLE(STRING("S"), STRING("E")) THEN
            maze[r][c] <- STRING("•")
        ENDIF
    ENDFOR
ENDFUNCTION

FUNCTION display_maze ACCEPTS(maze)
    FOR EACH row IN maze DO
        OUTPUT JOIN(row, EMPTY STRING)
    ENDFOR
ENDFUNCTION

FUNCTION create_grid ACCEPTS(rows, cols)
    IF (rows MODULUS 2) == 1 THEN
        carve_rows <- rows
    ELSE
        carve_rows <- rows - 1
    ENDIF
    IF (cols MODULUS 2) == 1 THEN
        carve_cols <- cols
    ELSE
        carve_cols <- cols - 1
    ENDIF
    maze <- EMPTY LIST
    FOR _ <- IN RANGE 0 TO rows DO
        maze_row <- EMPTY LIST
        FOR _ <- IN RANGE 0 TO cols DO
            APPEND STRING("▓") TO maze_row
        ENDFOR
        APPEND maze_row TO maze
    ENDFOR
        carve <- EMPTY LIST
    FOR _ <- IN RANGE 0 TO carve_rows DO
        carve_row <- EMPTY LIST
        FOR _ <- IN RANGE 0 TO carve_cols DO
            APPEND STRING("▓") TO carve_row
        ENDFOR
        APPEND carve_row TO carve
    ENDFOR
        CALL carve_maze(carve, carve_rows, carve_cols)
    FOR r <- IN RANGE 0 TO carve_rows DO
        FOR c <- IN RANGE 0 TO carve_cols DO
            maze[r][c] <- carve[r][c]
        ENDFOR
    ENDFOR
    maze[1][1] <- STRING("S")
    maze[carve_rows - 2][(carve_cols - 2)] <- STRING("E")
    path <- CALL solve_maze_bfs(maze, rows, cols)
    CALL mark_path(maze, path)
    CALL display_maze(maze)
    RETURN maze
ENDFUNCTION

CALL create_grid(11, 20)