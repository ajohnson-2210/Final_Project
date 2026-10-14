__reserved_keyword__string <- STRING("1a23")
string1 <- EMPTY STRING

FOR EACH __reserved_keyword__char IN __reserved_keyword__string DO
string1 <- string1 + CALL LOWERCASE(__reserved_keyword__char)
ENDFOR

__reserved_keyword__string <- STRING("45a6")
string2 <- EMPTY STRING

FOR EACH __reserved_keyword__char IN __reserved_keyword__string DO
string2 <- string2 + CALL LOWERCASE(__reserved_keyword__char)
ENDFOR

list1 <- CALL CHARACTERS_OF(string1)
list2 <- CALL CHARACTERS_OF(string2)

IF LENGTH OF list1 == 0 OR LENGTH OF list2 == 0 OR LENGTH OF list1 != LENGTH OF list2 THEN
OUTPUT STRING("string1 and string 2 are Not anagrams of each other")
QUIT
ENDIF

list1.sort()
list2.sort()

WHILE LENGTH OF list1 > 0 DO
x <- list1.pop()
y <- list2.pop()


IF x != y THEN
    OUTPUT STRING("string 1 and string 2 are Not anagrams of each other")
    QUIT
ENDIF


ENDWHILE

OUTPUT STRING("string 1 and string 2 Are anagrams of each other")