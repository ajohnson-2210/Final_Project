num <- 23
numCopy <- num
byteString <- EMPTY LIST
bits <- 0
WHILE (2 EXP bits) <= num DO
    bits <- bits + 1
ENDWHILE
IF bits < 7 THEN
    bits <- 7
ENDIF
WHILE bits >= 0 DO
    value <- 2 EXP bits
    IF value > num THEN
        APPEND 0 TO byteString
    ELSE
        APPEND 1 TO byteString
        num <- num - value
    ENDIF
    bits <- bits - 1
ENDWHILE
IF byteString[0] == 0 AND LENGTH OF byteString > 8 THEN
    byteString.pop(0)
ENDIF
bitString <- EMPTY STRING
FOR EACH bit IN byteString DO
    bitString <- bitString + CALL STRING(bit)
ENDFOR
OUTPUT STRING("{numCopy} = 0b {bitString}")