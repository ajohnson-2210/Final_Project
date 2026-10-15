FUNCTION unnamed_function ACCEPTS(N)
    FUNCTION Hanoi ACCEPTS(Discs, Source, Auxiliary, Destination)
        IF Discs == 1 THEN
            OUTPUT STRING("Move disk from {Source} to {Destination}")
        ELSE
            CALL Hanoi(Discs - 1, Source, Destination, Auxiliary)

            OUTPUT STRING("Move disk from {Source} to {Destination}")

            CALL Hanoi(Discs - 1, Auxiliary, Source, Destination)
        ENDIF
    ENDFUNCTION

    CALL Hanoi(N, STRING("A"), STRING("B"), STRING("C"))
ENDFUNCTION