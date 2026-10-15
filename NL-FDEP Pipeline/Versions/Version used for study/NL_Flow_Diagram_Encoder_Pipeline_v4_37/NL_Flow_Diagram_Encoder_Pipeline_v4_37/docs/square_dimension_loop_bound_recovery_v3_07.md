# GC208 — square-dimension loop-bound resolution

## Rule

Generic compatibility may resolve the exact source relationship:

```text
INPUT collection (D x D)
...
FOR i from 0 to D-1:
```

to the frozen AJ end-exclusive range:

```text
FOR i <- IN RANGE 0 TO LENGTH OF collection DO
```

This is a representation of source-stated shape information, not a new algorithm step. The implementation is corpus/model/algorithm/name independent.

## Deliberate exclusions

GC208 does not:

- create `D <- LENGTH OF collection`;
- resolve `R x C` rectangular annotations;
- rewrite loops beginning anywhere other than zero;
- rewrite upper bounds other than the exact inclusive `D - 1` form;
- override a separately supplied/assigned/bound `D`;
- choose between multiple collections annotated with the same dimension symbol;
- replace any other use of `D`.

The source annotation itself remains available until the established neutral-wrapper pass binds the declared collection as the function parameter.

## Semantics

AJ `IN RANGE 0 TO LENGTH OF collection` already has the required end-exclusive meaning, so Python lowering is directly `range(0, len(collection))`. No arithmetic simplification such as `(D - 1) + 1` and no synthetic dimension variable are required.
