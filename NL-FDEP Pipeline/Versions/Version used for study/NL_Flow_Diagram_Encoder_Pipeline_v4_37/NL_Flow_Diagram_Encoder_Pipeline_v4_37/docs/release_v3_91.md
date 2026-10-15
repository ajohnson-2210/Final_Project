# v3.91 — accumulated semantic-integrity corrections and character-predicate compiler tightening

v3.91 is the first numbered release after the v3.90 audit baseline because the final change in this batch modifies Python compiler behaviour. It also packages the normaliser/audit corrections deliberately accumulated in the v3.90 working tree without intermediate releases.

## 1. Retire implicit numeric-to-string repairs

GC230 and the duplicate GC158 modulus/string coercion are retired. Source-authored mixed additions such as `(n MOD 2) + result`, where `result` is string-backed but no `STRING(...)` conversion is supplied, remain mixed numeric/string operations. source_b, source_e, and source_a decimal-to-binary occurrences are therefore classified as expected executable-correctness failures rather than silently repaired. source_c's explicit `STRING(remainder)` remains executable. See `docs/source_b_algorithm2_source_numeric_string_expected_failure_audit.md`.

## 2. Tighten generic PUSH representation recovery

A generic `PUSH item TO receiver` no longer establishes that an unknown receiver is a LIST. Unknown representation is preserved canonically as `CALL PUSH(item, receiver)`; explicitly list-backed receivers may still become `APPEND`, and explicitly stack-backed receivers retain the PUSH abstraction. Python may use `.append(...)` as the implementation of the explicit PUSH abstraction. The structural GC124 two-stack recovery remains intact.

## 3. Record the GC245 set-plus evidence boundary

source_d Algorithm 41's `cols + {col}` and diagonal variants remain accepted as evidence-based non-mutating SET ADD/extension. The audit now records why this is justified: matching parameters are independently established as SET values, the right operands are singleton sets, membership use reinforces the type, and recursive state propagation requires non-mutating extension. The interpretation is explicitly refused outside that evidence pattern. See `docs/source_d_algorithm41_set_plus_as_add_audit.md`.

## 4. Remove compiler-side string coercion from character predicates

Canonical AJ remains:

```text
CALL is_digit(value)
CALL is_uppercase(value)
```

Python lowering changes from:

```python
str(value).isdigit()
str(value).isupper()
```

to:

```python
value.isdigit()
value.isupper()
```

The old compiler behaviour silently converted non-string inputs, inventing a conversion not supplied by source pseudocode. Non-string values now expose their type mismatch instead. source_d Algorithm 24 remains executable because `char` is independently evidenced as character/string data by `FOR EACH char IN password` before the explicit predicates are applied.

## Validation

- pytest: 972 passed, 3 skipped, 5 subtests passed
- unittest: 323 passed, 1 skipped
- AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
- AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`
- dialect change: none
- compiler change: yes (`is_digit` / `is_uppercase` direct method lowering)
