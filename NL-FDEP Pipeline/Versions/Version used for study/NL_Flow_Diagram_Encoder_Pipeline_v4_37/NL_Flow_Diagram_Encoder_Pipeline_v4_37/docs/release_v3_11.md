# NL-FDEP v3.11 release record

## Scope

v3.11 adds approved generic GC212 square-dimension identifier-reference recovery and records source_f Algorithm 27 as an expected executable-correctness failure caused by an unsupplied integer-division requirement.

## Production change

`pseudocode_profiles.py` adds GC212 immediately after GC208 and before neutral-wrapper/input normalisation.

Given a uniquely evidenced same-routine square annotation:

```text
INPUT collection (D x D)
```

remaining otherwise-unbound executable references to `D` may canonicalise directly to:

```text
LENGTH OF collection
```

GC208 continues to own its exact `0 .. D-1` loop-bound recovery and is unchanged.

GC212 is routine-scoped, refuses independent bindings and ambiguous annotations, and is string/comment/member/call-name safe. It never materialises `D <- LENGTH OF collection`.

## source_f Algorithm 27

The exact source now eliminates the previously unbound `N` from generated Python by resolving it through the explicit `(N x N)` matrix annotation.

The source outer bound still contains ordinary division:

```text
N / 2 - 1
```

which becomes only:

```text
LENGTH OF matrix / 2 - 1
```

The pipeline does not rewrite `/` to `INTEGER DIVISION`. Generated Python therefore retains `len(matrix) / 2`, and execution raises a float-range `TypeError`.

Classification:

**EXPECTED EXECUTABLE-CORRECTNESS FAILURE — SOURCE INTEGER-DIVISION REQUIREMENT NOT SUPPLIED**.

## Dialect

AJ_24038155 Dialect v1.1 remains frozen and unchanged.

## Validation

Working tree:

- pytest: **575 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**

Fresh extraction from packaged ZIP:

- pytest: **575 passed, 3 skipped, 5 subtests passed**
- unittest: **260 passed, 1 skipped**
- frozen AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
