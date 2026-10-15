# GC212 — square-dimension identifier-reference resolution

## Rule

Generic compatibility may use an explicit square-shape annotation:

```text
INPUT collection (D x D)
```

to resolve otherwise-unbound executable references to `D` in the same routine as:

```text
LENGTH OF collection
```

This is representation recovery for source-stated shape information. It does not create a new runtime dimension variable.

## Relationship to GC208

GC208 retains ownership of the exact historical loop-bound surface:

```text
FOR i from 0 to D-1:
```

which canonicalises directly to:

```text
FOR i <- IN RANGE 0 TO LENGTH OF collection DO
```

GC212 runs immediately afterwards and resolves only remaining references to the same evidenced dimension symbol, including occurrences inside compound expressions and index expressions.

Example:

```text
INPUT matrix (N x N)
matrix[N-1-j][i]
```

may become:

```text
matrix[LENGTH OF matrix-1-j][i]
```

## Guard conditions

GC212 applies only when:

- the shape annotation is a single-symbol square form `D x D`;
- the symbol identifies exactly one annotated collection in that routine scope;
- the symbol is not independently supplied as an input or routine parameter;
- the symbol is not independently assigned, used as a loop iterator, or bound as a catch identifier;
- the occurrence is executable identifier usage in that same routine.

GC212 does not rewrite:

- rectangular `R x C` annotations;
- ambiguous symbols associated with more than one collection in one routine;
- strings or comments;
- member/property names such as `object.D`;
- routine names such as `D()`;
- declaration surfaces;
- occurrences in a nested routine where the symbol has a different scope.

## Arithmetic boundary

GC212 replaces only the evidenced identifier reference. It does not alter surrounding arithmetic.

Therefore:

```text
D / 2
```

becomes:

```text
LENGTH OF collection / 2
```

and never:

```text
LENGTH OF collection INTEGER DIVISION 2
```

unless the source itself supplies integer division through an independently approved representation rule.

AJ_24038155 Dialect v1.1 remains unchanged.
