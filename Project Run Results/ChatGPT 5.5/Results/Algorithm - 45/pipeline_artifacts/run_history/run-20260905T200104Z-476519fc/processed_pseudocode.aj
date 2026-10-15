    INPUT MatrixA, MatrixB
    INPUT Rows, Columns

    FOR i <- 0 TO Rows-1
        FOR j <- 0 TO Columns-1
            Result[i][j] <- MatrixA[i][j] + MatrixB[i][j]
        ENDFOR
    ENDFOR

    OUTPUT Result
END