FUNCTION PATHFINDING(maze, start, end)
  graph <- []
  FOR cell IN maze
    IF cell IS NOT A WALL THEN
      graph <- graph + [cell]
    END IF
  END FOR