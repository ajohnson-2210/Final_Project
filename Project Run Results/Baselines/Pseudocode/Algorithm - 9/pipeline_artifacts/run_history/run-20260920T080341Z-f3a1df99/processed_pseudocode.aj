list1 <- LIST [5, 8, 1, 9, 3, 2, 4, 7, 6]
target <- 9
index <- 0
flag <- EMPTY STRING
FOR i <- IN RANGE 0 TO LENGTH OF list1 DO
    IF list1[i] == target THEN
        index <- i
        flag <- BOOLEAN(TRUE)
        BREAK
    ELSE
        flag <- BOOLEAN(FALSE)
    ENDIF
ENDFOR
IF flag == BOOLEAN(TRUE) THEN
    OUTPUT STRING("index of target is {index}")
ELSE
    OUTPUT STRING("{target} Is Not in the list!")
ENDIF