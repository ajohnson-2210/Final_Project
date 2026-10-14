numlist <- LIST [6, 7, 9, 4, 66, 8, 34, 5, 2]
OUTPUT numlist
n <- LENGTH OF numlist - 1
FOR i <- IN RANGE 0 TO n DO
    FOR j <- IN RANGE 0 TO (n - i) DO
        IF numlist[j] > numlist[j + 1] THEN
            temp <- numlist[j]
            numlist[j] <- numlist[j + 1]
            numlist[j + 1] <- temp
        ENDIF
    ENDFOR
ENDFOR
second_largest <- numlist[-2]
OUTPUT STRING("The Second highest number in the list = {second_largest}")