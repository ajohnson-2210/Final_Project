# v4.00 — lexical binding isolation for loop and catch variables

v4.00 extends the explicit AJ class-state/local-name boundary introduced in
v3.99 to every active canonical AJ construct that introduces an unqualified
local binding.

## Compiler change

AJ v1.2 makes instance state explicit through `THIS.property`.  Under v3.99,
ordinary assignment targets and parameters correctly shadowed same-spelled
class properties, but loop headers and named CATCH variables could still be
rendered through the class-field lookup path.

For example:

```text
CLASS Demo
PROPERTY item AS INTEGER
CONSTRUCTOR ACCEPTS()
PROPERTY THIS.item <- 0
ENDCONSTRUCTOR
METHOD total ACCEPTS(values)
FOR EACH item IN values DO
OUTPUT item
ENDFOR
RETURN THIS.item
ENDMETHOD
ENDCLASS
```

could incorrectly emit `for self.item in values:`.  v4.00 now collects all
lexical bindings for the current function/method/constructor scope before
Python emission.

The same rule is applied to the semantically equivalent binding sites:

- unqualified assignment targets;
- function/method/constructor parameters;
- `FOR EACH` loop variables;
- `FOR ... IN RANGE` loop variables;
- named `CATCH error` variables;
- nested `FUNCTION name ...` declarations (the declaration name binds locally).

Explicit `THIS.name` continues to compile as `self.name`.

## Collection-representation interaction

The same lexical binding analysis is also used by scoped collection-type
tracking.  A loop variable in a nested function therefore shadows a
same-spelled enclosing SET hint instead of accidentally inheriting `.add()`
behaviour.  Unshadowed enclosing collection evidence continues to work as in
v3.98.

## Guarded abstraction lookup

The same lexical-scope correction is applied to compiler guards for abstractions
whose semantics must be supplied explicitly (`isSafe`, `emptyBoard`,
`is_punctuation`, and ordered-cache helper operations). A nested helper
definition resolves calls only in its containing scope and descendants; it no
longer legitimises an unrelated sibling function's call. Module-level helpers
remain visible to nested scopes.

## Compatibility boundary

The older generic class-recovery path with no explicit AJ `PROPERTY`/`THIS`
syntax retains its existing evidence-based inferred-instance-state behaviour.
The new binding rule changes only explicit canonical AJ lexical resolution and
its already-scoped collection-representation environment.

## Dialect impact

None. AJ dialect v1.1 and v1.2 source documents are unchanged.

- AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
- AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`

## Validation

1009 pytest passed, 3 skipped, 5 subtests passed; 332 unittest passed, 1 skipped.
