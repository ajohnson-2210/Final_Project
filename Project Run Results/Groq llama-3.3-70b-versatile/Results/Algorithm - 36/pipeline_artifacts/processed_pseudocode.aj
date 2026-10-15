FUNCTION FIND_TARGET ACCEPTS(rotated_list, target)
  low <- 0
  high <- LENGTH OF rotated_list - 1
  WHILE low <= high DO
    mid <- (low + high) INTEGER DIVISION 2
    IF rotated_list[mid] == target THEN
      RETURN mid
    ELSE IF rotated_list[low] <= rotated_list[mid] THEN
      IF target >= rotated_list[low] AND target < rotated_list[mid] THEN
        high <- mid - 1
      ELSE
        low <- mid + 1
      ENDIF
    ELSE
      IF target > rotated_list[mid] AND target <= rotated_list[high] THEN
        low <- mid + 1
      ELSE
        high <- mid - 1
      ENDIF
    ENDIF
  ENDWHILE
  RETURN -1
ENDFUNCTION