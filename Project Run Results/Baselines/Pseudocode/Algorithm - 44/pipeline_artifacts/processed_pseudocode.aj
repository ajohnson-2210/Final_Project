COMMENT import random

FUNCTION kadane ACCEPTS(arr)
    n <- LENGTH OF arr
    current_sum <- arr[0]
    best_sum <- arr[0]
    current_start <- 0
    best_ranges <- LIST [TUPLE(0, 0)]
    i <- 1
    WHILE i < n DO
        IF (current_sum + arr[i]) < arr[i] THEN
            current_sum <- arr[i]
            current_start <- i
        ELSE
            current_sum <- current_sum + arr[i]
        ENDIF
        IF current_sum > best_sum THEN
            best_sum <- current_sum
            best_ranges <- LIST [TUPLE(current_start, i)]
        ELSE IF (current_sum == best_sum) THEN
            APPEND TUPLE(current_start, i) TO best_ranges
        ENDIF
        i <- i + 1
    ENDWHILE
    RETURN TUPLE(best_sum, best_ranges)
ENDFUNCTION

size <- RANDOM INT(5, 10)
arr <- EMPTY LIST
i <- 0
WHILE i < size DO
    IF RANDOM FLOAT(0, 1) < 0.5 THEN
        num <- RANDOM INT(-10, 10)
    ELSE
        num <- CALL round(RANDOM FLOAT(-10, 10), 2)
    ENDIF
    APPEND num TO arr
    i <- i + 1
ENDWHILE
OUTPUT STRING("Random array: {arr}")
kadane_result <- CALL kadane(arr)
best_sum <- kadane_result[0]
ranges <- kadane_result[1]
OUTPUT STRING("\nMaximum subarray sum: {best_sum}")
range_count <- LENGTH OF ranges
OUTPUT STRING("Number of max subarrays: {range_count}")
idx <- 0
WHILE idx < LENGTH OF ranges DO
    current_range <- ranges[idx]
    start <- current_range[0]
    end <- current_range[1]
    subarray_number <- idx + 1
    IF idx == 0 THEN
        OUTPUT STRING("\nSubarray {subarray_number} Start Index: {start}: ")
    ELSE
        OUTPUT STRING("Subarray {subarray_number} Start Index: {start}: ")
    ENDIF
    j <- start
    subarray_text <- EMPTY STRING
    WHILE j <= end DO
        subarray_text <- subarray_text + CALL STRING(arr[j]) + STRING(", ")
        j <- j + 1
    ENDWHILE
    OUTPUT subarray_text
    idx <- idx + 1
ENDWHILE