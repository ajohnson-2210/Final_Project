FUNCTION maxSubarraySum ACCEPTS(arr)
    maxEndingHere <- 0
    maxSoFar <- CALL negative_infinity()
    FOR EACH num IN arr DO
        maxEndingHere <- CALL max(num, maxEndingHere + num)
        maxSoFar <- CALL max(maxSoFar, maxEndingHere)
    ENDFOR
    RETURN maxSoFar
ENDFUNCTION