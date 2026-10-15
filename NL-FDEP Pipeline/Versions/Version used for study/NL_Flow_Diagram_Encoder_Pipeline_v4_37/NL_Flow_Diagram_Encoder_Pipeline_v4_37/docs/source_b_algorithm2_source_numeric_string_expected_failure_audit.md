# source_b Algorithm 2 — source numeric/string expected-failure audit

## Motivating occurrence

```text
FUNCTION decimalToBinary(n):
    IF n == 0 THEN RETURN "0"
    result <- ""
    WHILE n > 0:
        result <- (n MOD 2) + result
        n <- n DIV 2
    RETURN result
```

## Preserved type boundary

The source explicitly initialises `result` as a string and then explicitly adds the numeric result of `n MOD 2` to that string:

```text
(n MOD 2) + result
```

There is no source-authored string conversion around the modulus result. Compatibility normalisation therefore preserves the operation as:

```text
result <- (n MODULUS 2) + result
```

and generated Python preserves the mixed-type addition:

```python
result = (n % 2) + result
```

For every positive input, execution reaches this expression and raises `TypeError` because Python cannot add an integer directly to a string.

The former GC230 behaviour inserted `to_string(...)` around the modulus result. That made the program executable, but it repaired a source-authored type error and therefore concealed a defect that the study is intended to observe. GC230 is retired from active normalisation.

## Counterfactual viability audit

The surrounding decimal-to-binary algorithm is otherwise viable. As an **audit-only counterfactual**, changing only the missing conversion so that the source-equivalent operation becomes:

```text
STRING(n MOD 2) + result
```

corresponding to:

```python
str(n % 2) + result
```

allows the otherwise unchanged algorithm to return the correct binary representation for the tested values `0..4096`.

This counterfactual is evidence for diagnosis only. It is **not** applied by production normalisation or compilation.

## Explicit-conversion control

source_c Algorithm 2 explicitly supplies the conversion:

```text
remainder = n MOD 2
binaryString = STRING(remainder) + binaryString
```

That source is legitimately normalised to `CALL to_string(remainder)` and compiles to `str(remainder)`. The contrast demonstrates that the pipeline accepts the conversion when the source provides it and refuses to invent it when the source omits it.

## Audit classification

source_b Algorithm 2: **EXPECTED EXECUTABLE-CORRECTNESS FAILURE — SOURCE NUMERIC-TO-STRING CONVERSION NOT SUPPLIED**.

- source modulus arithmetic preserved: YES
- implicit numeric-to-string repair: NO
- GC230 active coercion: NO (retired)
- generated Python exposes mixed `int + str`: YES
- surrounding algorithm otherwise viable with explicit conversion: YES, audit-only counterfactual evidence
- explicit source `STRING(...)` conversion supported: YES
- compiler change: NO
- dialect change: NO

## Analogous source_e occurrence

source_e Algorithm 2 contains the same omitted conversion in function-shaped arithmetic form:

```text
binary = MOD(n, 2) + binary
n = FLOOR(n / 2)
```

`MOD(n, 2)` is legitimately normalised to modulus arithmetic and `FLOOR(n / 2)` is legitimately represented as integer division for this non-negative decimal-to-binary loop. Neither operation supplies a string conversion. The generated mixed numeric/string addition is therefore preserved and the positive-input execution is classified as the same expected source failure. An audit-only insertion of `str(...)` makes the otherwise unchanged source_e algorithm produce the expected binary results.

## Analogous source_a occurrence

source_a Algorithm 2 separates the modulus into a numeric variable but then performs the same unsupported concatenation:

```text
Remainder <- Number MOD 2
Binary <- Remainder + Binary
```

Because `Binary` is explicitly initialised as a string and `Remainder` is explicitly numeric, inserting a string conversion would again repair the source rather than normalise it. The production path preserves the mixed-type addition and execution is an expected failure for positive input. An audit-only `str(Remainder)` counterfactual produces the expected binary output without changing the surrounding algorithm.

Across the corpus, source_b, source_e and source_a therefore provide three independent examples of the omitted numeric-to-string conversion defect; source_c provides the contrasting explicit-conversion case.
