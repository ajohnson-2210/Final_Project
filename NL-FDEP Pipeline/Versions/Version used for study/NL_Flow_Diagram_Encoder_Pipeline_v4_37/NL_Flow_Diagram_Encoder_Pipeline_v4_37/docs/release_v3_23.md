# NL-FDEP v3.23 release record

## Summary

v3.23 adds the approved source_c 2 numeric-to-string compatibility recovery while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC225 — evidenced numeric STRING conversion

GC225 does not reinterpret `STRING(expression)` globally. Frozen AJ continues to use quoted `STRING("...")` as its string-literal syntax.

The rule activates only when all of the following source evidence is present in the same routine:

- a destination is explicitly initialised as `EMPTY STRING`;
- an identifier is independently produced by a `MOD`/`MODULUS` assignment and is therefore numeric;
- the exact assignment prepends `STRING(identifier)` to that same string accumulator.

That explicit source conversion is represented as `CALL to_string(identifier)`, using the already-existing compiler intrinsic that lowers to Python `str(identifier)`. No arithmetic, loop, digit, or binary-conversion logic is invented.

## source_c 2 canonical result

```text
FUNCTION decimalToBinary ACCEPTS(n)
    IF n == 0 THEN
        RETURN STRING("0")
    ENDIF
    binaryString <- EMPTY STRING
    WHILE n > 0 DO
        remainder <- n MODULUS 2
        binaryString <- CALL to_string(remainder) + binaryString
        n <- n INTEGER DIVISION 2
    ENDWHILE
    RETURN binaryString
ENDFUNCTION
```

The resulting Python uses `str(remainder)` and is trustworthy for the source-stated non-negative integer input domain.

AJ_24038155 Dialect v1.1 is unchanged.

## Working-tree validation

- pytest: **670 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**

