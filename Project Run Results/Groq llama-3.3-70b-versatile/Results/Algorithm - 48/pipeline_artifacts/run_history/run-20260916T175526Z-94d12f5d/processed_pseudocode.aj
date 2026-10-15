FUNCTION FIND_FILE(directory, file_type)
  files <- []
  FOR item IN directory
    IF item IS A FILE AND item.endswith(file_type) THEN
      files <- files + [item]
    ELSE IF item IS A DIRECTORY THEN
      files <- files + FIND_FILE(item, file_type)
    END IF
  END FOR
  RETURN files
END FUNCTION