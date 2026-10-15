# source_e Algorithm 15 audit — v2.99

## Motivating occurrence

source_e Algorithm 15 initialises both running sentinels with the explicit mathematical value name `NEGATIVE_INFINITY`:

```text
FUNCTION SECOND_LARGEST(arr)
  max = NEGATIVE_INFINITY
  second_max = NEGATIVE_INFINITY
  FOR num IN arr
    IF num > max THEN
      second_max = max
      max = num
    ELSE IF num > second_max AND num != max THEN
      second_max = num
    END IF
  END FOR
  RETURN second_max
END FUNCTION
```

The source supplies the complete second-largest algorithm. The only incompatibility is the spelling of the negative-infinity sentinel.

## Recovery

The pipeline already canonicalised the explicit surface `-infinity` to:

```text
CALL negative_infinity()
```

v2.99 accepts `NEGATIVE_INFINITY` as an additional case-insensitive representational synonym on assignment RHSs. No second-largest logic is reconstructed.

Canonical AJ includes:

```text
max <- CALL negative_infinity()
second_max <- CALL negative_infinity()
```

and the existing compiler emits `float('-inf')`.

## Classification

**PASS AFTER CONSERVATIVE NEGATIVE-INFINITY REPRESENTATION RECOVERY**

- semantic inference: NO NEW SEMANTIC INFERENCE
- algorithmic reconstruction: NO
- source logic correction: NO
- dialect change: NO
