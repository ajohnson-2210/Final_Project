OUTPUT STRING("Binary Search in O(log n) Time")

FUNCTION rsearch ACCEPTS(nums, target)
    left <- 0
    right <- LENGTH OF nums - 1
    WHILE left <= right DO
        mid <- (left + right) INTEGER DIVISION 2
        mid_val <- nums[mid]
        IF mid_val == target THEN
            RETURN mid
        ENDIF
        IF nums[left] <= mid_val THEN
            IF nums[left] <= target AND target < mid_val THEN
                right <- mid - 1
            ELSE
                left <- mid + 1
            ENDIF
        ELSE IF (mid_val < target) AND (target <= nums[right]) THEN
            left <- mid + 1
        ELSE
            right <- mid - 1
        ENDIF
    ENDWHILE
    RETURN STRING("Target Value Does Not Exist")
ENDFUNCTION

nums <- LIST [4, 5, 6, 1, 2, 3]
OUTPUT nums
OUTPUT CALL rsearch(nums, 1)
OUTPUT CALL rsearch(nums, 5)
OUTPUT CALL rsearch(nums, 9)