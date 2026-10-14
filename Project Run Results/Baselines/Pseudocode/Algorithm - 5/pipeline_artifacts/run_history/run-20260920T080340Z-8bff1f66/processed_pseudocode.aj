COMMENT import string

string1 <- STRING("This /_@!^*%<>is &*;:'a sentence, that has punctuation!")
string2 <- EMPTY LIST
FOR EACH character IN string1 DO
    APPEND character TO string2
ENDFOR
x <- EMPTY LIST
FOR EACH s IN string2 DO
    filtered_chars <- EMPTY LIST
    FOR EACH __reserved_keyword__char IN s DO
        IF __reserved_keyword__char NOT IN string_method_punctuation THEN
            APPEND __reserved_keyword__char TO filtered_chars
        ENDIF
    ENDFOR
    APPEND JOIN(filtered_chars, EMPTY STRING) TO x
ENDFOR
final <- JOIN(x, EMPTY STRING)
OUTPUT final