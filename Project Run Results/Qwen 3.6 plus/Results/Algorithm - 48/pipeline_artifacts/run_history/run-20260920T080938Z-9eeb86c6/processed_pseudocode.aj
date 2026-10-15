FUNCTION search(directory, targetExt):
    results <- []

    FOR item in directory.contents:
        IF item is file AND item.ext == targetExt:
            results.add(item)
        ELSE IF item is directory:
            results.extend(search(item, targetExt))

    RETURN results