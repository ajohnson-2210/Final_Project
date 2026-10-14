OUTPUT STRING("Towers Of Hanoi")

FUNCTION display_board ACCEPTS(pegs, n)
    level <- n - 1
    WHILE level >= 0 DO
        row <- EMPTY STRING
        IF level < LENGTH OF pegs[STRING("A")] THEN
            peg_value_1 <- pegs[STRING("A")][level]
            row <- row + STRING("  ") + CALL STRING(peg_value_1) + STRING("  ")
        ELSE
            row <- row + STRING("  |  ")
        ENDIF
        IF level < LENGTH OF pegs[STRING("B")] THEN
            peg_value_2 <- pegs[STRING("B")][level]
            row <- row + STRING("  ") + CALL STRING(peg_value_2) + STRING("  ")
        ELSE
            row <- row + STRING("  |  ")
        ENDIF
        IF level < LENGTH OF pegs[STRING("C")] THEN
            peg_value_3 <- pegs[STRING("C")][level]
            row <- row + STRING("  ") + CALL STRING(peg_value_3) + STRING("  ")
        ELSE
            row <- row + STRING("  |  ")
        ENDIF
        OUTPUT row
        level <- level - 1
    ENDWHILE
    OUTPUT STRING("  A    B    C\n")
ENDFUNCTION

FUNCTION move_between ACCEPTS(pegs, a, b, n)
    IF LENGTH OF pegs[a] == 0 THEN
        disc <- pegs[b].pop()
        APPEND disc TO pegs[a]
        OUTPUT STRING("Move disc {disc} from {b} to {a}\n")
    ELSE IF (LENGTH OF pegs[b] == 0) THEN
        disc <- pegs[a].pop()
        APPEND disc TO pegs[b]
        OUTPUT STRING("Move disc {disc} from {a} to {b}\n")
    ELSE IF (pegs[a][-1] < pegs[b][-1]) THEN
        disc <- pegs[a].pop()
        APPEND disc TO pegs[b]
        OUTPUT STRING("Move disc {disc} from {a} to {b}\n")
    ELSE
        disc <- pegs[b].pop()
        APPEND disc TO pegs[a]
        OUTPUT STRING("Move disc {disc} from {b} to {a}\n")
    ENDIF
    CALL display_board(pegs, n)
ENDFUNCTION

FUNCTION hanoi ACCEPTS(n, pegs)
    A <- STRING("A")
    B <- STRING("B")
    C <- STRING("C")
    IF (n MODULUS 2) == 0 THEN
        swap_values <- TUPLE(C, B)
        B <- swap_values[0]
        C <- swap_values[1]
    ENDIF
    total_moves <- (2 EXP n) - 1
    CALL display_board(pegs, n)
    move <- 1
    WHILE move <= total_moves DO
        IF (move MODULUS 3) == 1 THEN
            CALL move_between(pegs, A, C, n)
        ELSE IF ((move MODULUS 3) == 2) THEN
            CALL move_between(pegs, A, B, n)
        ELSE
            CALL move_between(pegs, B, C, n)
        ENDIF
        move <- move + 1
    ENDWHILE
    OUTPUT STRING("Solved!!")
ENDFUNCTION

N <- 0
loop <- BOOLEAN(TRUE)
WHILE loop DO
    TRY
        N <- CALL INTEGER(INPUT(STRING("Enter number of discs: ")))
        N <- CALL INTEGER(N)
        OUTPUT STRING("Setting up..\n")
        loop <- BOOLEAN(FALSE)
    CATCH
        OUTPUT STRING("Than's Not a Valid Number, Please Try Again!!\n")
    ENDTRY
ENDWHILE
pegs <- EMPTY DICTIONARY
peg_a_values <- EMPTY LIST
FOR disk <- IN RANGE N TO 0 STEP -1 DO
    APPEND disk TO peg_a_values
ENDFOR
pegs[STRING("A")] <- peg_a_values
pegs[STRING("B")] <- EMPTY LIST
pegs[STRING("C")] <- EMPTY LIST
CALL hanoi(N, pegs)