    INPUT Text

    Reverse <- ""

    FOR i <- LENGTH(Text)-1 DOWNTO 0
        Reverse <- Reverse + Text[i]
    ENDFOR

    OUTPUT Reverse
END