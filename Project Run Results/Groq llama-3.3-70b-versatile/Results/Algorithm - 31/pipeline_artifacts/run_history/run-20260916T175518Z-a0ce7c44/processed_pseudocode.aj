FUNCTION CO_REFERENCE_RESOLUTION ACCEPTS(text)
  COMMENT Use a co-reference resolution algorithm to identify relationships
  relationships <- CALL IDENTIFY_RELATIONSHIPS(text)
  RETURN relationships
ENDFUNCTION