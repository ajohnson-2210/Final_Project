FUNCTION safe_placement ACCEPTS(board, row, col, n)
    r <- 0
    WHILE r < row DO
        IF board[r] == col THEN
            RETURN BOOLEAN(FALSE)
        ENDIF
        r <- r + 1
    ENDWHILE
    r <- row - 1
    c <- col - 1
    WHILE r >= 0 AND c >= 0 DO
        IF board[r] == c THEN
            RETURN BOOLEAN(FALSE)
        ENDIF
        r <- r - 1
        c <- c - 1
    ENDWHILE
    r <- row - 1
    c <- col + 1
    WHILE r >= 0 AND c < n DO
        IF board[r] == c THEN
            RETURN BOOLEAN(FALSE)
        ENDIF
        r <- r - 1
        c <- c + 1
    ENDWHILE
    RETURN BOOLEAN(TRUE)
ENDFUNCTION

FUNCTION solve_n_queens_util ACCEPTS(board, row, n, solutions)
    IF row == n THEN
        board_copy <- EMPTY LIST
        FOR EACH column IN board DO
            APPEND column TO board_copy
        ENDFOR
        APPEND board_copy TO solutions
        RETURN
    ENDIF
    col <- 0
    WHILE col < n DO
        IF CALL safe_placement(board, row, col, n) THEN
            board[row] <- col
            CALL solve_n_queens_util(board, (row + 1), n, solutions)
            board[row] <- -1
        ENDIF
        col <- col + 1
    ENDWHILE
ENDFUNCTION

FUNCTION solve_n_queens ACCEPTS(n)
    board <- EMPTY LIST
    FOR fill_index <- IN RANGE 0 TO n DO
        APPEND -1 TO board
    ENDFOR
        solutions <- EMPTY LIST
    CALL solve_n_queens_util(board, 0, n, solutions)
    RETURN solutions
ENDFUNCTION

FUNCTION print_board ACCEPTS(solution)
    n <- LENGTH OF solution
    r <- 0
    WHILE r < n DO
        row_str <- EMPTY STRING
        c <- 0
        WHILE c < n DO
            IF solution[r] == c THEN
                row_str <- row_str + STRING("Q ")
            ELSE
                row_str <- row_str + STRING(". ")
            ENDIF
            c <- c + 1
        ENDWHILE
        OUTPUT row_str
        r <- r + 1
    ENDWHILE
    OUTPUT EMPTY STRING
ENDFUNCTION

FUNCTION print_all_solutions ACCEPTS(solutions)
    total <- LENGTH OF solutions
    OUTPUT STRING("\nShowing ALL {total} solutions:\n")
    i <- 0
    WHILE i < total DO
        solution_number <- i + 1
        OUTPUT STRING("Solution {solution_number}:")
        CALL print_board(solutions[i])
        i <- i + 1
    ENDWHILE
ENDFUNCTION

N <- CALL INTEGER(INPUT(STRING("Enter board size N: ")))
solutions <- CALL solve_n_queens(N)
total <- LENGTH OF solutions
OUTPUT STRING("\nSolved {N}-Queens.")
OUTPUT STRING("Total solutions: {total}\n")
index <- 0
WHILE BOOLEAN(TRUE) DO
    OUTPUT STRING("Menu:")
    OUTPUT STRING("  1 - Show current solution")
    OUTPUT STRING("  2 - Next solution")
    OUTPUT STRING("  3 - Previous solution")
    OUTPUT STRING("  4 - Go to solution number")
    OUTPUT STRING("  5 - Show ALL solutions")
    OUTPUT STRING("  6 - Quit")
    choice <- INPUT(STRING("Enter choice: ")).strip()
    IF choice == STRING("1") THEN
        IF total > 0 THEN
            solution_number <- index + 1
            OUTPUT STRING("\nShowing solution {solution_number} of {total}:\n")
            CALL print_board(solutions[index])
        ELSE
            OUTPUT STRING("\nNo solutions exist for this N.\n")
        ENDIF
    ELSE IF (choice == STRING("2")) THEN
        IF total > 0 THEN
            index <- (index + 1) MODULUS total
            solution_number <- index + 1
            OUTPUT STRING("\nShowing solution {solution_number} of {total}:\n")
            CALL print_board(solutions[index])
        ELSE
            OUTPUT STRING("\nNo solutions.\n")
        ENDIF
    ELSE IF (choice == STRING("3")) THEN
        IF total > 0 THEN
            index <- (index - 1) MODULUS total
            solution_number <- index + 1
            OUTPUT STRING("\nShowing solution {solution_number} of {total}:\n")
            CALL print_board(solutions[index])
        ELSE
            OUTPUT STRING("\nNo solutions.\n")
        ENDIF
    ELSE IF (choice == STRING("4")) THEN
        IF total > 0 THEN
            num <- INPUT(STRING("Enter solution number: ")).strip()
            IF num.isdigit() THEN
                num <- CALL INTEGER(num)
                IF 1 <= num AND num <= total THEN
                    index <- num - 1
                    solution_number <- index + 1
                    OUTPUT STRING("\nShowing solution {solution_number} of {total}:\n")
                    CALL print_board(solutions[index])
                ELSE
                    OUTPUT STRING("\nInvalid number.\n")
                ENDIF
            ELSE
                OUTPUT STRING("\nInvalid input.\n")
            ENDIF
        ELSE
            OUTPUT STRING("\nNo solutions.\n")
        ENDIF
    ELSE IF (choice == STRING("5")) THEN
        CALL print_all_solutions(solutions)
    ELSE IF (choice == STRING("6")) THEN
        OUTPUT STRING("\nExiting program.\n")
        BREAK
    ELSE
        OUTPUT STRING("\nInvalid option.\n")
    ENDIF
ENDWHILE