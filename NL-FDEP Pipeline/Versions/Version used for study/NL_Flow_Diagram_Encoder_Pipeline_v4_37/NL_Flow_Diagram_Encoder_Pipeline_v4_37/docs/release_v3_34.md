# NL-FDEP v3.34 release record

## Scope

v3.34 implements the approved source_d Algorithm 20 square-root representation recovery while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC233 explicit square-root exponentiation

source_d Algorithm 20 explicitly uses `SQUARE_ROOT(n)` as the upper bound of its divisor-search loop. The approved representation is mathematical square root expressed as exponentiation by `0.5`. AJ v1.1 already provides the `EXP` operator, and the deterministic Python compiler already lowers `EXP` to `**`.

GC233 therefore recognises only a free single-argument `SQUARE_ROOT(value)` expression and represents it as:

```text
(value EXP 0.5)
```

which lowers deterministically to Python:

```python
(value ** 0.5)
```

GC233 refuses routine declarations named `SQUARE_ROOT`, member-method calls, quoted text, zero-argument calls and multi-argument calls. It does not insert `INTEGER`, `int(...)`, floor, truncation, rounding, or any other coercion.

## source_d Algorithm 20 boundary

The square-root expression now canonicalises, parses, encodes to a flow diagram, and compiles deterministically. The supplied algorithm separately uses that square-root value as the inclusive endpoint of a generic range loop. Generic inclusive-range recovery correctly preserves the source endpoint by adding one before lowering to Python `range(...)`, but Python range endpoints must be integer-valued. Because GC233 intentionally preserves square root as `(n ** 0.5)`, calling the compiled source_d Algorithm 20 still raises `TypeError` at the range boundary.

That remaining failure is deliberately visible. v3.34 does not infer floor/integer conversion semantics that were not part of the approved GC233 change.

## Validation

- targeted source_d 20 / GC233 regression and refusal-boundary tests: 4 passed;
- full pytest suite: 729 passed, 3 skipped, 5 subtests passed;
- unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 729 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
