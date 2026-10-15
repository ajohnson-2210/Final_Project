CLASS STACK ACCEPTS()
  CONSTRUCTOR ACCEPTS()
    array <- EMPTY LIST
    top <- -1

  ENDCONSTRUCTOR
  METHOD PUSH ACCEPTS(element)
    top <- top + 1
    array[top] <- element

  ENDMETHOD
  METHOD POP ACCEPTS()
    IF top == -1 THEN
      RETURN NULL
    ENDIF
    element <- array[top]
    top <- top - 1
    RETURN element

  ENDMETHOD
  METHOD PEEK ACCEPTS()
    IF top == -1 THEN
      RETURN NULL
    ENDIF
    RETURN array[top]

  ENDMETHOD
ENDCLASS