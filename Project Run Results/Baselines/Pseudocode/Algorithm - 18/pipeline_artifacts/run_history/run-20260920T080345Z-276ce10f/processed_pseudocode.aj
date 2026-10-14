string1 <- STRING("This is a Sentence, that needs the chars counted!!")
stringlist <- EMPTY LIST
FOR EACH character IN string1 DO
    APPEND character TO stringlist
ENDFOR
countlist <- EMPTY DICTIONARY
WHILE LENGTH OF stringlist > 0 DO
    __reserved_keyword__char <- stringlist.pop(0)
    IF __reserved_keyword__char NOT IN countlist THEN
        countlist[__reserved_keyword__char] <- 1
    ELSE
        countlist[__reserved_keyword__char] <- countlist[__reserved_keyword__char] + 1
    ENDIF
ENDWHILE
FOR EACH entry IN countlist.items() DO
    key <- entry[0]
    val <- entry[1]
    OUTPUT STRING("Character {key} appears {val} times")
ENDFOR