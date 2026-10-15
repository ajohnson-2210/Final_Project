FUNCTION INTERSECTION ACCEPTS(arr1, arr2)
  i <- 0
  j <- 0
  intersection <- EMPTY LIST
  WHILE i < LENGTH OF arr1 AND j < LENGTH OF arr2 DO
    IF arr1[i] == arr2[j] THEN
      APPEND arr1[i] TO intersection
      i <- i + 1
      j <- j + 1
    ELSE IF arr1[i] < arr2[j] THEN
      i <- i + 1
    ELSE
      j <- j + 1
    ENDIF
  ENDWHILE
  RETURN intersection
ENDFUNCTION