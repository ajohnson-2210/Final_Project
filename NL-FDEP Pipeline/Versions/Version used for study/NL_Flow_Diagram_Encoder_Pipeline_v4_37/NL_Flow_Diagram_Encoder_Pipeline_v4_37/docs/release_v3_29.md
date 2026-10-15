# NL-FDEP v3.29 release record

## Scope

v3.29 implements the approved source_b Algorithm 15 pipeline fix while leaving the frozen AJ_24038155 Dialect v1.1 unchanged and introducing no new compatibility meaning.

## GC079 / GC151 chained-assignment composition fix

GC079 already expands a source chained assignment such as:

```text
largest <- second <- expression
```

into two ordinary assignments:

```text
second <- expression
largest <- second
```

GC151 already represents explicit negative-infinity assignment sentinels such as `-INFINITY` and `NEGATIVE_INFINITY` as:

```text
CALL negative_infinity()
```

In v3.28, GC151 was checked before GC079 on each source line. Therefore the chained source:

```text
largest <- second <- -INFINITY
```

was expanded too late for GC151 and incorrectly remained:

```text
second <- -INFINITY
largest <- second
```

which compiled to an unbound Python `INFINITY` identifier.

v3.29 completes the existing GC151 recovery at the exact GC079 split point, yielding:

```text
second <- CALL negative_infinity()
largest <- second
```

The generated Python uses `float('-inf')`. The change is deliberately restricted to the negative-infinity surfaces already accepted by GC151. It does not recursively re-normalise arbitrary GC079 output and does not reinterpret positive infinity identifiers, member properties, or unrelated right-hand expressions.

## source_b Algorithm 15

The supplied second-largest algorithm now parses, compiles, and executes with the intended shared negative-infinity initialisation. Representative positive and negative input arrays return the expected distinct second-largest value.

## Validation

- targeted chained-assignment / negative-infinity regression and boundary tests: pass;
- full pytest suite: 704 passed, 3 skipped, 5 subtests passed;
- unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 704 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
