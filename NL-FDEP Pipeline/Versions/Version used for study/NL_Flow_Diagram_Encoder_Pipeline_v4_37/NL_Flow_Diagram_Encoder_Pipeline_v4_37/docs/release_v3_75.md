# Release v3.75 — GC121 array-stack backing inference retired

## Problem

source_a Algorithm 37 declares an array-backed stack only as:

```text
CREATE Stack
Top <- -1
```

and later performs indexed writes such as:

```text
Top <- Top + 1
Stack[Top] <- Item
```

GC121 previously rewrote `CREATE Stack` to:

```text
Stack <- EMPTY LIST
```

This invented a dynamic-list backing representation that the source never supplied. It also produced a representation inconsistent with the supplied indexed-write algorithm: a Python empty list does not already contain index `0` for `Stack[0] <- Item`.

## Change

GC121 remains a structural recovery for the implicit `PUSH`, `POP`, and `PEEK` operation boundaries, but it no longer assigns any storage representation to `CREATE Stack`.

The canonicalised compatibility source therefore retains:

```text
CREATE Stack
Top <- -1

FUNCTION PUSH ACCEPTS(Item)
    Top <- Top + 1
    Stack[Top] <- Item
ENDFUNCTION
```

Because `CREATE Stack` is not AJ v1.2 syntax and no capacity/dimensions are supplied, strict parsing stops before Python generation. No `EMPTY LIST`, `APPEND`, `REMOVE LAST ITEM`, `LENGTH`, class wrapper, or scope declaration is invented to rescue the algorithm.

Explicit list-backed source remains unchanged and valid; this retirement applies only to GC121's former inference from abstract `CREATE Stack`.

source_a Algorithm 37 is now an intentional expected failure. Algorithm 38 remains the previously documented expected failure after GC122 retirement, so the source_a aggregate parse floor changes from 37 to 36 and the regression test names both failures explicitly.

## Validation

- focused GC121/source-integrity tests: 8 passed
- pytest: 913 passed, 3 skipped, 5 subtests passed
- unittest: 309 passed, 1 skipped
- historical AJ v1.1 SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
- active AJ v1.2 SHA-256: `414a1510d616f23e3c7a34945c16d52ad6c0b7f9bf591c66e6408c3329ef0348`
