FUNCTION unnamed_function ACCEPTS(IP_List)
        UniqueIPs <- EMPTY SET

        FOR EACH IP IN IP_List DO
            CALL add_to_set(UniqueIPs, IP)
        ENDFOR

        OUTPUT UniqueIPs
ENDFUNCTION