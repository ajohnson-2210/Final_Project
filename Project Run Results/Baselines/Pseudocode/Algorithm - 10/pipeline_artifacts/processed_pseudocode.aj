vowel <- LIST [STRING("a"), STRING("e"), STRING("i"), STRING("o"), STRING("u")]
text <- STRING("This is a sentence that contains vowels")
a <- 0
e <- 0
i <- 0
o <- 0
u <- 0
textlist <- EMPTY LIST
FOR EACH character IN text DO
    APPEND character.lower() TO textlist
ENDFOR
FOR b <- IN RANGE 0 TO LENGTH OF textlist DO
    FOR j <- IN RANGE 0 TO LENGTH OF vowel DO
        IF vowel[j] == textlist[b] THEN
            IF j == 0 THEN
                a <- a + 1
                BREAK
            ELSE IF (j == 1) THEN
                e <- e + 1
                BREAK
            ELSE IF (j == 2) THEN
                i <- i + 1
                BREAK
            ELSE IF (j == 3) THEN
                o <- o + 1
                BREAK
            ELSE IF (j == 4) THEN
                u <- u + 1
                BREAK
            ENDIF
        ENDIF
    ENDFOR
ENDFOR
OUTPUT STRING("The text contains the vowel a {a} times")
OUTPUT STRING("The text contains the vowel e {e} times")
OUTPUT STRING("The text contains the vowel i {i} times")
OUTPUT STRING("The text contains the vowel o {o} times")
OUTPUT STRING("The text contains the vowel u {u} times")