# NL-FDEP v3.35 release record

## Scope

v3.35 implements the approved source_d Algorithm 24 character-predicate representation recovery while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC234 explicit character predicates

source_d Algorithm 24 explicitly calls `IS_DIGIT(char)` and `IS_UPPERCASE(char)` while validating a password. The pipeline already provides the compatibility intrinsics `is_digit(value)` and `is_uppercase(value)`, with deterministic Python lowering to `str(value).isdigit()` and `str(value).isupper()`.

GC234 therefore recognises only the exact free single-argument forms and represents them as:

```text
IS_DIGIT(value)     -> CALL is_digit(value)
IS_UPPERCASE(value) -> CALL is_uppercase(value)
```

The recovery refuses routine declarations named `IS_DIGIT`/`IS_UPPERCASE`, member-method calls, quoted-text matches, zero-argument calls and multi-argument calls. It does not broaden either predicate beyond the explicit source operation.

## source_d Algorithm 24 result

The supplied password validator now canonicalises, parses, encodes to a flow diagram, compiles deterministically, and executes with the supplied semantics: at least eight characters, at least one digit, and at least one uppercase character.

## Validation

- targeted source_d 24 / GC234 regression and refusal-boundary tests: 4 passed;
- full pytest suite: 733 passed, 3 skipped, 5 subtests passed;
- unittest suite: 260 passed, 1 skipped;
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`;
- fresh-extraction rerun: 733 passed, 3 skipped, 5 subtests passed; 260 unittest passed, 1 skipped.
