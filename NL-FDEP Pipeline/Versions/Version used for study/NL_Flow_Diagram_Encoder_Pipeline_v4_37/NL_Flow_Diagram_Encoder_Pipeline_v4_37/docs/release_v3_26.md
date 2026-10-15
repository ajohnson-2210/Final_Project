# NL-FDEP v3.26 release record

## Summary

v3.26 implements the approved source_e 8 explicit alphabetical sort-mode compatibility recovery while leaving the frozen AJ_24038155 Dialect v1.1 unchanged.

## GC228 — explicit `ALPHABETICAL_ORDER` sort mode

GC228 recognises the exact free two-argument form `SORT(value, ALPHABETICAL_ORDER)` when `value` is a simple identifier. `ALPHABETICAL_ORDER` is treated as an explicit ascending alphabetical sort-mode marker rather than an undeclared runtime identifier. The call is routed through the existing `sort_value` compatibility intrinsic, which lowers to Python `sorted(value)` and is semantically equivalent to `sorted(value, reverse=False)`.

The rule does not reinterpret arbitrary comparator expressions, descending markers, member methods, other arities, or non-simple first arguments. No sorting algorithm is invented; the source explicitly supplies both the SORT operation and the alphabetical-order mode.

AJ_24038155 Dialect v1.1 is unchanged.

## Validation

- targeted source_e 8 + prior source_e 5 regressions: **10 passed**
- full pytest: **686 passed, 3 skipped, 5 subtests passed**
- full unittest: **260 passed, 1 skipped**
- frozen AJ dialect SHA-256: `0d4dcdbb5a28eb5be11f72a7152e4ed55bb2296733a994573bbce50a3a862598`
