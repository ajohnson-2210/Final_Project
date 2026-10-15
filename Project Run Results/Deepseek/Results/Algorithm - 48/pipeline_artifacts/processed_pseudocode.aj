FUNCTION findFilesByType(directory, fileExtension):
    results <- empty list
    FOR each item in directory:
        IF item IS a file:
            IF item.extension == fileExtension:
                results.__reserved_keyword__append(item.path)
        ELSE IF item IS a directory:
            // Recursive call
            subResults <- findFilesByType(item, fileExtension)
            results.extend(subResults)
    RETURN results