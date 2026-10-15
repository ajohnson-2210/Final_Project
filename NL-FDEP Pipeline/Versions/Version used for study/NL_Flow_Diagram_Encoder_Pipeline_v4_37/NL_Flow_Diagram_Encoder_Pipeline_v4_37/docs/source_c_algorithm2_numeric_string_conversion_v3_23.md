# source_c Algorithm 2 numeric string-conversion recovery — v3.23

## Source shape

source_c supplies a complete decimal-to-binary loop. Its explicit `STRING(remainder)` operation is conversion-like because `remainder` is produced by `n MOD 2` and is prepended to an accumulator initialised as the empty string.

## GC225

GC225 treats that exact evidence combination as a compatibility representation of numeric-to-text conversion:

```text
remainder <- n MODULUS 2
binaryString <- STRING(remainder) + binaryString
```

becomes:

```text
remainder <- n MODULUS 2
binaryString <- CALL to_string(remainder) + binaryString
```

The existing compiler then emits `str(remainder)`. The rule refuses quoted string literals, identifiers without numeric evidence, destinations without explicit string backing, and unrelated `STRING(...)` contexts.

## Runtime contract

source_c explicitly states that the decimal input is non-negative. Within that domain, the supplied repeated remainder/prepend/integer-division algorithm returns the standard binary representation, including the explicit zero case.

## Classification

**PASS AFTER SOURCE-EVIDENCED TYPE-CONVERSION RECOVERY — TRUSTWORTHY EXECUTABLE FOR NON-NEGATIVE INTEGER INPUTS**
