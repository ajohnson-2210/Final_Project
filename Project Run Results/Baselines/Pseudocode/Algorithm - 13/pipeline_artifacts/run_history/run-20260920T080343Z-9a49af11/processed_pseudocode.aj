__reserved_keyword__string <- STRING("This is a sentence that needs reversing")
stringlist <- EMPTY LIST
FOR EACH character IN __reserved_keyword__string DO
    APPEND character TO stringlist
ENDFOR
revlist <- EMPTY STRING
OUTPUT __reserved_keyword__string
FOR x <- IN RANGE 0 TO LENGTH OF stringlist DO
    i <- stringlist.pop(-1)
    revlist <- revlist + i
ENDFOR
OUTPUT revlist