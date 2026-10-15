FUNCTION maxSubarraySum ACCEPTS(arr)
    maxSum <- arr[0]
    currentSum <- arr[0]
    FOR i <- IN RANGE 1 TO (LENGTH OF arr - 1) + 1 DO
        currentSum <- CALL max(arr[i], currentSum + arr[i])
        maxSum <- CALL max(maxSum, currentSum)
    ENDFOR
    RETURN maxSum
ENDFUNCTION