FUNCTION SearchFiles ACCEPTS(directory, target_extension)
    matching_files <- EMPTY LIST

    FOR EACH item IN directory.getItems() DO
        IF item.isFolder() THEN
            matching_files.extend(CALL SearchFiles(item, target_extension))
        ELSE IF item.getExtension() == target_extension THEN
            APPEND item.path TO matching_files
        ENDIF
    ENDFOR

    RETURN matching_files
ENDFUNCTION