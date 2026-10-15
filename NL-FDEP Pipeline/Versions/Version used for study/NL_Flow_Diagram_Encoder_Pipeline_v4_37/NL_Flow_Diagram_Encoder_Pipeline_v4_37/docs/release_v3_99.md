# v3.99 — explicit class-state and local-name scope isolation

v3.99 fixes a compiler semantic defect in canonical AJ class name resolution.
An unqualified name assigned inside a canonical `METHOD` or `CONSTRUCTOR` no
longer becomes instance state merely because a class property has the same
identifier spelling.

## Compiler change

AJ v1.2 makes instance state explicit through `THIS.property` and
`PROPERTY THIS.property <- value`.  Under v3.98, a class such as:

```text
CLASS Demo
PROPERTY value AS INTEGER
CONSTRUCTOR ACCEPTS()
PROPERTY THIS.value <- 1
ENDCONSTRUCTOR
METHOD local_test ACCEPTS()
value <- 5
RETURN value
ENDMETHOD
ENDCLASS
```

could incorrectly emit `self.value = 5` and `return self.value` for the method.
The compiler now preserves the source distinction:

- explicit `THIS.value` remains instance state (`self.value`);
- unqualified method/constructor assignment targets remain local bindings;
- parameters continue to shadow same-spelled properties;
- nested functions inside a class preserve outer lexical locals and can shadow
  class properties with their own parameters/assignments.

## Legacy compatibility boundary

Older generic-compatibility recovery can produce classes with no explicit
`PROPERTY`/`THIS` syntax whose constructor and methods use unqualified names as
object state.  That pre-existing evidence-based compatibility path is retained:
constructor-backed names referenced across those recovered methods continue to
compile as `self.<name>`.

The new local-shadowing rule therefore applies to explicit canonical AJ state
without breaking legacy inferred-state recovery.

## Dialect impact

None. AJ dialect v1.1 and v1.2 source documents are unchanged.

- AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
- AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`

## Validation

1001 pytest passed, 3 skipped, 5 subtests passed; 332 unittest passed, 1 skipped.
