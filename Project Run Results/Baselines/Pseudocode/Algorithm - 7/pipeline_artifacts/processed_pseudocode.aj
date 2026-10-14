COMMENT import string

string1 <- STRING("This is a sentence!")
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
word <- EMPTY STRING
words <- EMPTY LIST
flag <- BOOLEAN(TRUE)
delimiter <- STRING(" ")
WHILE flag DO
    TRY
        element <- x.pop(0)
        IF element != delimiter THEN
            word <- word + element
        ELSE
            APPEND word TO words
            word <- EMPTY STRING
        ENDIF
    CATCH
        APPEND word TO words
        flag <- BOOLEAN(FALSE)
    ENDTRY
ENDWHILE
OUTPUT words