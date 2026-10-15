# v4.03 — frozen collection-grammar completion

v4.03 implements frozen AJ v1.2 collection forms that were already normative in the dialect but previously absent from the executable parser/compiler pipeline. The release covers both collection statements and canonical set expressions.

## Parser and AST support

The parser now accepts:

```text
INSERT value INTO collection AT index
REMOVE value FROM collection
```

with dedicated `InsertNode` and `RemoveValueNode` AST forms. The flow-diagram encoder serialises and labels both as process operations.

`INSERT`, `INTO`, `AT`, `REMOVE`, and `FROM` are handled contextually for these statement forms rather than being made globally reserved lexer words. This preserves existing source identifiers and compatibility-normalised method names such as `METHOD Remove`. The longer existing `REMOVE FIRST ITEM FROM` and `REMOVE LAST ITEM FROM` phrases retain lexer precedence.

### Set literals and set operations

The parser now also accepts the frozen AJ forms:

```text
SET [value1, value2]
UNION(set1, set2)
INTERSECTION(set1, set2)
DIFFERENCE(set1, set2)
```

with dedicated `SetLiteralNode` and `SetOperationNode` AST forms. Empty `SET []` is supported and compiles to Python `set()`. Operation names are contextual in expression position, so identifiers such as `FUNCTION Union ...` remain legal outside operation syntax.

## Static semantics

The new statements use the existing conservative evidence boundary:

- `INSERT` requires LIST when the receiver type is statically known; unknown receiver types remain unresolved rather than guessed.
- a statically known INSERT index must be INTEGER; unknown index types remain unresolved.
- `REMOVE value FROM collection` accepts statically known LIST or SET receivers and rejects statically known incompatible receivers such as DICTIONARY or scalar values.
- no existence check or recovery branch is invented for specific-value removal.
- set operations require SET operands when operand types are statically known; unknown operand types remain unresolved rather than guessed.

## Python compiler lowering

Canonical AJ lowers directly to the corresponding Python collection operations:

```text
INSERT item INTO values AT index
```

becomes:

```python
values.insert(index, item)
```

and:

```text
REMOVE item FROM values
```

becomes:

```python
values.remove(item)
```

The `.remove(...)` lowering is shared by LIST and SET representations and preserves normal Python failure when the requested value is absent. The compiler does not silently guard, ignore, or repair that source operation.

Canonical set expressions lower directly to Python set semantics:

```text
SET [INTEGER(1), INTEGER(2)]    -> {1, 2}
SET []                           -> set()
UNION(a, b)                      -> (a | b)
INTERSECTION(a, b)               -> (a & b)
DIFFERENCE(a, b)                 -> (a - b)
```

Assignments from a SET literal or set operation establish SET representation evidence for subsequent generic AJ `APPEND`, so later mutation correctly lowers to `.add(...)`.

## Packaged static-semantic refinements since v4.02

These validated changes did not independently trigger a package because they did not alter Python compiler lowering. They are included in v4.03 because this release does contain a compiler change.

### Lexically resolved function arity

Calls to AJ functions whose declarations are visible in lexical scope now require exactly the declared number of required parameters. Recursive, nested, shadowed, sibling, and forward-declared AJ functions are covered. Undefined/external helpers remain unchecked because their signatures are not supplied.

### Narrow explicit-known-type validation

Static validation now rejects only type incompatibilities that are already provable from AJ evidence, including incompatible known arithmetic operands, known non-Boolean IF/WHILE conditions, non-INTEGER indexes on a known LIST, definitely unhashable keys on a known DICTIONARY, incompatible explicit homogeneous-list elements, and incompatible known collection receivers. Unknown parameter/receiver types remain unknown rather than being inferred.

### Constructor valued-return rejection

A constructor may use a value-less `RETURN` for early exit, but `RETURN expression` is now a static expected failure. Returns inside nested functions or ordinary methods retain their own routine semantics.

## Dialect impact

None. AJ dialect v1.1 and v1.2 source documents are unchanged.

- AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
- AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`

## Validation

1095 pytest passed, 3 skipped, 5 subtests passed; 332 unittest passed, 1 skipped.
